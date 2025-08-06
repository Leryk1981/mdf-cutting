"""
API для интеграции AI-модуля с основной системой.

Этот модуль содержит:
- API для получения корректировок
- Интеграция с основной системой раскроя
- Обратная связь для улучшения модели
"""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import json
import torch
import numpy as np
from datetime import datetime
import logging

from ..core.models import EnsembleCorrectionModel, HybridCorrectionModel
from ..core.leftover_optimizer import LeftoverOptimizer, LeftoverOptimizationModel
from ..features.geometry import GeometryFeatureExtractor
from ..features.optimization import OptimizationFeatureExtractor
from ..features.leftovers import Leftover, LeftoverFeatureExtractor
from ..utils.data_loader import MLDataLoader
from ..utils.metrics import CorrectionMetrics
from src.mdf_cutting.config.loader import ConfigLoader

logger = logging.getLogger(__name__)


class CorrectionAPI:
    """API для интеграции AI-модуля с основной системой"""
    
    def __init__(self, model_path: Optional[Path] = None, config_loader: Optional[ConfigLoader] = None):
        self.config_loader = config_loader or ConfigLoader()
        self.config_loader.load_all()
        
        # Инициализация компонентов
        self.geometry_extractor = GeometryFeatureExtractor()
        self.optimization_extractor = OptimizationFeatureExtractor()
        self.leftover_extractor = LeftoverFeatureExtractor()
        self.data_loader = MLDataLoader(self.config_loader)
        self.metrics = CorrectionMetrics()
        
        # Инициализация оптимизатора остатков
        self.leftover_optimizer = None
        
        # База данных остатков (в реальности это будет БД)
        self.leftovers_db = self._load_leftovers_db()
        
        # Загрузка модели
        self.model_path = model_path or Path("models/trained/best_model.pth")
        self.model = self._load_model()
        
        # Конфигурация устройства
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        
        # Логирование
        self.logger = logging.getLogger("correction_api")
        logging.basicConfig(level=logging.INFO)
    
    def get_corrections(self, dxf_path: Path, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Основной метод получения AI-корректировок"""
        try:
            start_time = datetime.now()
            
            # 1. Загрузка и парсинг данных
            self.logger.info(f"Processing DXF: {dxf_path}")
            dxf_data = self.data_loader.load_dxf(dxf_path)
            
            # 2. Извлечение признаков
            geometry_features = self.geometry_extractor.extract_features(dxf_data)
            optimization_features = self.optimization_extractor.extract_features(dxf_data, order_data)
            
            # 3. Подготовка данных для модели
            model_input = self._prepare_model_input(geometry_features, optimization_features)
            
            # 4. Получение предсказаний
            predictions = self._predict(model_input)
            
            # 5. Генерация корректировок
            corrections = self._generate_corrections(predictions, dxf_data)
            
            # 6. Оценка качества
            quality_metrics = self.metrics.evaluate_correction(
                original_data=dxf_data,
                predictions=predictions,
                features=geometry_features
            )
            
            # 7. Формирование ответа
            processing_time = (datetime.now() - start_time).total_seconds()
            
            response = {
                "status": "success",
                "corrections": corrections,
                "quality_metrics": quality_metrics,
                "model_info": {
                    "confidence": predictions.get("confidence", 0.0),
                    "model_version": "v1.0",
                    "processing_time_ms": int(processing_time * 1000)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Successfully processed {dxf_path} in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing {dxf_path}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "dxf_file": str(dxf_path),
                "timestamp": datetime.now().isoformat()
            }
    
    def batch_process(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Пакетная обработка нескольких запросов"""
        results = []
        
        for request in requests:
            try:
                result = self.get_corrections(
                    dxf_path=Path(request["dxf_path"]),
                    order_data=request["order_data"]
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "status": "error",
                    "error": str(e),
                    "request": request
                })
        
        return results
    
    def apply_corrections(self, dxf_path: Path, corrections: List[Dict[str, Any]], 
                         output_path: Optional[Path] = None) -> Path:
        """Применение корректировок к DXF файлу"""
        if output_path is None:
            output_path = dxf_path.with_suffix(f".corrected{dxf_path.suffix}")
        
        try:
            import ezdxf
            
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()
            
            # Применение каждой корректировки
            for correction in corrections:
                piece_id = correction.get("piece_id")
                params = correction.get("parameters", {})
                
                # Поиск детали по ID
                piece = self._find_piece_by_id(msp, piece_id)
                if piece:
                    self._apply_transformation(piece, params)
            
            doc.saveas(output_path)
            self.logger.info(f"Corrections applied successfully. Saved to {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error applying corrections: {str(e)}")
            raise
    
    def feedback_loop(self, correction_result: Dict[str, Any]):
        """Обратная связь для улучшения модели (RL)"""
        # Здесь может быть логика для обновления модели на основе 
        # обратной связи от пользователя о качестве корректировок
        success = correction_result.get("success", False)
        applied_corrections = correction_result.get("applied_corrections", [])
        
        if success:
            # Сохраняем успешный опыт для будущего обучения
            self._store_positive_experience(applied_corrections)
        else:
            # Сохраняем неудачный опыт для анализа
            self._store_negative_experience(applied_corrections)
    
    def _load_model(self) -> Union[EnsembleCorrectionModel, HybridCorrectionModel]:
        """Загрузка обученной модели"""
        try:
            checkpoint = torch.load(self.model_path, map_location='cpu')
            
            # Восстановление архитектуры на основе конфигурации
            model_config = checkpoint.get("config", {})
            model_type = model_config.get("model_type", "ensemble")
            
            if model_type == "ensemble":
                model = EnsembleCorrectionModel(
                    feature_dims=model_config["feature_dims"],
                    num_models=model_config.get("num_models", 3)
                )
            elif model_type == "hybrid":
                prediction_model = CorrectionPredictionModel(
                    feature_dims=model_config["feature_dims"]
                )
                rl_model = CorrectionReinforcementModel(
                    state_dim=model_config["rl_state_dim"],
                    action_dim=model_config["rl_action_dim"]
                )
                model = HybridCorrectionModel(prediction_model, rl_model)
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            model.load_state_dict(checkpoint["model_state_dict"])
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            raise RuntimeError(f"Model loading failed: {str(e)}")
    
    def _prepare_model_input(self, geometry_features: Dict, optimization_features: Dict) -> Dict[str, torch.Tensor]:
        """Подготовка входных данных для модели"""
        # Преобразование словарей в тензоры
        input_data = {}
        
        # Глобальные признаки
        global_np = np.array([
            geometry_features["global_features"]["utilization_rate"],
            geometry_features["global_features"]["waste_percentage"],
            geometry_features["global_features"]["pieces_complexity"]
        ])
        input_data["global"] = torch.FloatTensor(global_np)
        
        # Локальные признаки (агрегированные)
        local_features = geometry_features["local_features"]["pieces_features"]
        if local_features:
            local_np = np.array([
                np.mean([f["compactness"] for f in local_features]),
                np.mean([f["aspect_ratio"] for f in local_features]),
                np.std([f["min_dist_to_edge"] for f in local_features])
            ])
        else:
            local_np = np.zeros(3)
        input_data["local"] = torch.FloatTensor(local_np)
        
        # Оптимизационные признаки
        optim_np = np.array([
            optimization_features.get("total_cut_length", 0),
            optimization_features.get("piece_size_variance", 0),
            optimization_features.get("utilization_rate", 0)
        ])
        input_data["optimization"] = torch.FloatTensor(optim_np)
        
        return input_data
    
    def _predict(self, model_input: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """Получение предсказаний от модели"""
        with torch.no_grad():
            # Перемещение данных на устройство и добавление batch dimension
            input_on_device = {
                k: v.unsqueeze(0).to(self.device) 
                for k, v in model_input.items()
            }
            
            # Предсказание
            outputs = self.model(input_on_device)
            
            # Постобработка результатов
            if isinstance(self.model, EnsembleCorrectionModel):
                return self._process_ensemble_output(outputs)
            elif isinstance(self.model, HybridCorrectionModel):
                return self._process_hybrid_output(outputs)
    
    def _process_ensemble_output(self, outputs: Dict) -> Dict[str, Any]:
        """Обработка выхода ансамбля моделей"""
        params = outputs["correction_params"].cpu().numpy()[0]
        confidence = outputs["improvement_score"].item()
        
        # Определение типа корректировки
        types = ["position", "rotation", "scaling", "custom"]
        type_probs = torch.softmax(outputs["correction_type"], dim=-1).cpu().numpy()[0]
        correction_type = types[np.argmax(type_probs)]
        
        return {
            "correction_type": correction_type,
            "parameters": {
                "dx": float(params[0]),
                "dy": float(params[1]),
                "rotation": float(params[2]),
                "scale_x": float(params[3]),
                "scale_y": float(params[4])
            },
            "confidence": confidence,
            "type_probabilities": {types[i]: float(type_probs[i]) for i in range(len(types))}
        }
    
    def _generate_corrections(self, predictions: Dict, dxf_data: Dict) -> List[Dict[str, Any]]:
        """Генерация списка корректировок на основе предсказаний"""
        corrections = []
        
        # Эвристика: если высокая уверенность и значительное улучшение
        if predictions["confidence"] > 0.7 and predictions.get("improvement_potential", 0) > 0.1:
            # Ищем детали с низким качеством расположения
            for entity in dxf_data.get("entities", []):
                if entity.get("type") in ["LWPOLYLINE", "POLYLINE"]:
                    # Простая эвристика для определения проблемных деталей
                    if self._is_problematic_piece(entity, dxf_data):
                        correction = {
                            "piece_id": entity.get("handle", ""),
                            "piece_type": entity.get("type"),
                            "correction_type": predictions["correction_type"],
                            "parameters": predictions["parameters"],
                            "confidence": predictions["confidence"],
                            "expected_improvement": predictions.get("improvement_potential", 0)
                        }
                        corrections.append(correction)
        
        return corrections
    
    def _is_problematic_piece(self, piece: Dict, dxf_data: Dict) -> bool:
        """Простая эвристика для определения проблемных деталей"""
        # Здесь может быть более сложная логика
        # Например, проверка близости к краю листа или пересечений
        
        # Упрощенная реализация
        piece_area = piece.get("area", 0)
        return piece_area > 100 and piece_area < 10000  # Примерный диапазон
    
    def _find_piece_by_id(self, msp, piece_id: str):
        """Поиск детали по идентификатору в DXF"""
        for entity in msp:
            if hasattr(entity, 'dxf') and entity.dxf.handle == piece_id:
                return entity
        return None
    
    def _apply_transformation(self, piece, params: Dict[str, float]):
        """Применение трансформации к детали"""
        dx = params.get("dx", 0)
        dy = params.get("dy", 0)
        rotation = params.get("rotation", 0)
        scale_x = params.get("scale_x", 1)
        scale_y = params.get("scale_y", 1)
        
        # Применение трансформаций через ezdxf
        if dx != 0 or dy != 0:
            piece.translate(dx, dy)
        
        if rotation != 0:
            piece.rotate(rotation)
        
        if scale_x != 1 or scale_y != 1:
            piece.scale(scale_x, scale_y)
    
    def _store_positive_experience(self, corrections: List[Dict]):
        """Сохранение положительного опыта для RL"""
        # Реализация зависит от конкретной архитектуры RL
        pass
    
    def _store_negative_experience(self, corrections: List[Dict]):
        """Сохранение отрицательного опыта для RL"""
        # Реализация зависит от конкретной архитектуры RL
        pass
    
    def optimize_with_leftovers(self, dxf_path: Path, order_data: Dict[str, Any], 
                              force_new_sheets: bool = False) -> Dict[str, Any]:
        """Оптимизация раскроя с учетом остатков."""
        try:
            start_time = datetime.now()
            
            # 1. Загрузка и базовый анализ
            dxf_data = self.data_loader.load_dxf(dxf_path)
            geometry_features = self.geometry_extractor.extract_features(dxf_data)
            
            # 2. Анализ остатков
            leftover_features = self.leftover_extractor.extract_leftover_features(
                dxf_data, self.leftovers_db
            )
            
            # 3. Определение стратегии
            strategy = leftover_features["optimization_strategy"]
            
            # Если принудительно требуются новые листы или нет подходящих остатков
            if (force_new_sheets or 
                len(leftover_features["material_efficiency"]["suitable_leftovers"]) == 0):
                # Используем базовый AI без остатков
                result = self.get_corrections(dxf_path, order_data)
                result["optimization_strategy"] = "new_sheets_only"
                return result
            
            # 4. Инициализация оптимизатора остатков
            if self.leftover_optimizer is None:
                self.leftover_optimizer = self._init_leftover_optimizer()
            
            # 5. Оптимизация с остатками
            optimization_result = self.leftover_optimizer.optimize_layout(
                dxf_data, self.leftovers_db
            )
            
            # 6. Формирование итогового результата
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "success",
                "optimization_strategy": "with_leftovers",
                "assignments": optimization_result["assignments"],
                "optimized_layout": optimization_result["optimized_layout"],
                "new_leftovers": optimization_result["new_leftovers"],
                "efficiency_metrics": optimization_result["efficiency_metrics"],
                "material_analysis": leftover_features["material_efficiency"],
                "suitable_leftovers": leftover_features["leftover_suitability"],
                "processing_time_ms": int(processing_time * 1000),
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Optimized with leftovers in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in leftover optimization: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "optimization_strategy": "with_leftovers"
            }
    
    def update_leftovers_db(self, new_leftovers: List[Dict[str, Any]]):
        """Обновление базы данных остатками после раскроя."""
        try:
            for leftover_data in new_leftovers:
                # Преобразование в объект Leftover
                leftover = Leftover(
                    id=f"leftover_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.leftovers_db)}",
                    geometry=leftover_data.get("geometry"),
                    material_code=leftover_data.get("material_code", "MDF"),
                    thickness=leftover_data.get("thickness", 16.0),
                    creation_date=datetime.now().isoformat(),
                    source_dxf=leftover_data.get("source_dxf", ""),
                    usage_count=0,
                    priority=leftover_data.get("priority", 1.0),
                    area=leftover_data.get("area_remaining", 0.0),
                    width=leftover_data.get("width", 0.0),
                    height=leftover_data.get("height", 0.0)
                )
                
                # Добавление в базу
                self.leftovers_db.append(leftover)
            
            self.logger.info(f"Added {len(new_leftovers)} new leftovers to database")
            
        except Exception as e:
            self.logger.error(f"Error updating leftovers database: {e}")
    
    def get_leftovers_usage_stats(self) -> Dict[str, Any]:
        """Статистика использования остатков."""
        try:
            if not self.leftovers_db:
                return {"message": "No leftovers in database"}
            
            total_leftovers = len(self.leftovers_db)
            used_leftovers = sum(1 for l in self.leftovers_db if l.usage_count > 0)
            avg_usage = np.mean([l.usage_count for l in self.leftovers_db])
            
            # Статистика по размерам
            areas = [l.area for l in self.leftovers_db]
            avg_area = np.mean(areas)
            total_area = sum(areas)
            
            return {
                "total_leftovers": total_leftovers,
                "used_leftovers": used_leftovers,
                "unused_leftovers": total_leftovers - used_leftovers,
                "usage_rate": used_leftovers / total_leftovers if total_leftovers > 0 else 0,
                "average_usage_count": avg_usage,
                "average_area": avg_area,
                "total_area": total_area,
                "material_distribution": self._get_material_distribution()
            }
        except Exception as e:
            self.logger.error(f"Error getting leftovers stats: {e}")
            return {"error": str(e)}
    
    def _load_leftovers_db(self) -> List[Leftover]:
        """Загрузка базы данных остатков."""
        # В реальности это будет загрузка из БД
        # Для примера - пустая база
        return []
    
    def _init_leftover_optimizer(self) -> LeftoverOptimizer:
        """Инициализация оптимизатора остатков."""
        try:
            # Загрузка предобученной модели
            model_path = Path("models/trained/leftover_optimizer.pth")
            feature_dim = 256
            
            model = LeftoverOptimizationModel(feature_dim=feature_dim)
            
            if model_path.exists():
                checkpoint = torch.load(model_path, map_location='cpu')
                model.load_state_dict(checkpoint["model_state_dict"])
                self.logger.info("Loaded trained leftover optimizer")
            else:
                self.logger.warning("Could not load trained leftover optimizer, using untrained model")
            
            config = {"device": str(self.device)}
            
            return LeftoverOptimizer(model, config)
            
        except Exception as e:
            self.logger.error(f"Error initializing leftover optimizer: {e}")
            # Fallback к базовой модели
            model = LeftoverOptimizationModel()
            config = {"device": str(self.device)}
            return LeftoverOptimizer(model, config)
    
    def _get_material_distribution(self) -> Dict[str, int]:
        """Распределение остатков по материалам."""
        distribution = {}
        for leftover in self.leftovers_db:
            material = leftover.material_code
            distribution[material] = distribution.get(material, 0) + 1
        return distribution