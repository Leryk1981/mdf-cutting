"""
Метрики оценки качества корректировок.

Этот модуль содержит:
- Метрики для оценки корректировок
- Анализ эффективности оптимизации
- Сравнение с эталонными решениями
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import logging
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

logger = logging.getLogger(__name__)


class CorrectionMetrics:
    """Метрики для оценки качества корректировок карт раскроя"""
    
    def __init__(self):
        """Инициализация метрик."""
        self.metrics_history = []
    
    def evaluate_correction(self, original_data: Dict[str, Any], 
                          predictions: Dict[str, Any],
                          features: Dict[str, Any]) -> Dict[str, float]:
        """
        Оценка качества корректировок.
        
        Args:
            original_data: Исходные данные карты раскроя
            predictions: Предсказания модели
            features: Извлеченные признаки
            
        Returns:
            Dict: Словарь с метриками качества
        """
        try:
            # Базовые метрики предсказаний
            prediction_metrics = self._evaluate_predictions(predictions)
            
            # Метрики геометрической эффективности
            geometric_metrics = self._evaluate_geometric_improvement(
                original_data, predictions, features
            )
            
            # Метрики оптимизации
            optimization_metrics = self._evaluate_optimization_quality(
                original_data, predictions, features
            )
            
            # Комплексная оценка
            overall_score = self._calculate_overall_score(
                prediction_metrics, geometric_metrics, optimization_metrics
            )
            
            metrics = {
                **prediction_metrics,
                **geometric_metrics,
                **optimization_metrics,
                "overall_score": overall_score
            }
            
            # Сохраняем историю
            self.metrics_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Ошибка оценки корректировок: {e}")
            return self._get_default_metrics()
    
    def _evaluate_predictions(self, predictions: Dict[str, Any]) -> Dict[str, float]:
        """Оценка качества предсказаний модели."""
        metrics = {}
        
        try:
            # Оценка параметров корректировки
            if "correction_params" in predictions:
                params = predictions["correction_params"]
                
                # Статистики параметров
                metrics["params_mean"] = float(np.mean(params))
                metrics["params_std"] = float(np.std(params))
                metrics["params_range"] = float(np.max(params) - np.min(params))
                
                # Оценка разумности параметров
                metrics["params_reasonableness"] = self._assess_params_reasonableness(params)
            
            # Оценка уверенности
            if "confidence" in predictions:
                confidence = predictions["confidence"]
                metrics["confidence_score"] = float(confidence)
                metrics["confidence_reliability"] = self._assess_confidence_reliability(confidence)
            
            # Оценка типа корректировки
            if "correction_type" in predictions:
                correction_type = predictions["correction_type"]
                metrics["correction_type_confidence"] = self._assess_type_confidence(correction_type)
            
        except Exception as e:
            logger.warning(f"Ошибка оценки предсказаний: {e}")
        
        return metrics
    
    def _evaluate_geometric_improvement(self, original_data: Dict[str, Any],
                                      predictions: Dict[str, Any],
                                      features: Dict[str, Any]) -> Dict[str, float]:
        """Оценка геометрического улучшения."""
        metrics = {}
        
        try:
            # Анализ исходных геометрических признаков
            original_global = features.get("global_features", {})
            original_utilization = original_global.get("utilization_rate", 0)
            original_waste = original_global.get("waste_percentage", 100)
            
            # Оценка потенциального улучшения
            if "improvement_score" in predictions:
                improvement_potential = predictions["improvement_score"]
                
                # Ожидаемое улучшение утилизации
                expected_utilization = original_utilization + (improvement_potential * 20)  # До 20% улучшения
                expected_waste = max(0, original_waste - (improvement_potential * 15))  # До 15% снижения отходов
                
                metrics["expected_utilization_improvement"] = expected_utilization - original_utilization
                metrics["expected_waste_reduction"] = original_waste - expected_waste
                metrics["improvement_potential"] = float(improvement_potential)
            
            # Оценка геометрической сложности
            metrics["geometric_complexity"] = self._assess_geometric_complexity(original_data)
            
            # Оценка пространственной эффективности
            metrics["spatial_efficiency"] = self._assess_spatial_efficiency(features)
            
        except Exception as e:
            logger.warning(f"Ошибка оценки геометрического улучшения: {e}")
        
        return metrics
    
    def _evaluate_optimization_quality(self, original_data: Dict[str, Any],
                                     predictions: Dict[str, Any],
                                     features: Dict[str, Any]) -> Dict[str, float]:
        """Оценка качества оптимизации."""
        metrics = {}
        
        try:
            # Анализ признаков оптимизации
            optimization_features = features.get("optimization_features", {})
            
            # Оценка эффективности резки
            cutting_efficiency = optimization_features.get("cutting_efficiency", 0)
            metrics["cutting_efficiency_score"] = cutting_efficiency
            
            # Оценка использования материала
            material_efficiency = optimization_features.get("material_efficiency", 0)
            metrics["material_efficiency_score"] = material_efficiency
            
            # Оценка технологической осуществимости
            feasibility_score = self._assess_technical_feasibility(predictions, features)
            metrics["technical_feasibility"] = feasibility_score
            
            # Оценка экономической эффективности
            economic_score = self._assess_economic_efficiency(predictions, features)
            metrics["economic_efficiency"] = economic_score
            
            # Комплексная оценка оптимизации
            optimization_score = (
                0.3 * cutting_efficiency +
                0.3 * material_efficiency +
                0.2 * feasibility_score +
                0.2 * economic_score
            )
            metrics["overall_optimization_score"] = optimization_score
            
        except Exception as e:
            logger.warning(f"Ошибка оценки качества оптимизации: {e}")
        
        return metrics
    
    def _assess_params_reasonableness(self, params: List[float]) -> float:
        """Оценка разумности параметров корректировки."""
        if not params:
            return 0.0
        
        # Нормализуем параметры
        params_np = np.array(params)
        
        # Проверяем диапазоны (в мм и градусах)
        reasonable_ranges = {
            0: 50,   # dx: ±50 мм
            1: 50,   # dy: ±50 мм
            2: 15,   # rotation: ±15 градусов
            3: 0.2,  # scale_x: ±20%
            4: 0.2   # scale_y: ±20%
        }
        
        reasonableness_scores = []
        for i, (param, max_range) in enumerate(reasonable_ranges.items()):
            if i < len(params_np):
                param_value = abs(params_np[i])
                if param_value <= max_range:
                    score = 1.0 - (param_value / max_range)
                else:
                    score = 0.0
                reasonableness_scores.append(score)
        
        return np.mean(reasonableness_scores) if reasonableness_scores else 0.0
    
    def _assess_confidence_reliability(self, confidence: float) -> float:
        """Оценка надежности уверенности."""
        # Высокая уверенность должна быть обоснованной
        if confidence > 0.8:
            # Проверяем, не слишком ли высокая уверенность
            return 0.9 if confidence < 0.95 else 0.7
        elif confidence > 0.5:
            return 0.8
        else:
            return 0.6
    
    def _assess_type_confidence(self, correction_type: str) -> float:
        """Оценка уверенности в типе корректировки."""
        # Простые типы корректировок более надежны
        type_confidence = {
            "position": 0.9,
            "rotation": 0.8,
            "scaling": 0.7,
            "custom": 0.6
        }
        
        return type_confidence.get(correction_type, 0.5)
    
    def _assess_geometric_complexity(self, original_data: Dict[str, Any]) -> float:
        """Оценка геометрической сложности."""
        try:
            entities = original_data.get("entities", [])
            
            # Подсчет различных типов сущностей
            entity_types = {}
            for entity in entities:
                entity_type = entity.get("type", "unknown")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            # Оценка сложности на основе разнообразия и количества
            total_entities = len(entities)
            type_diversity = len(entity_types)
            
            # Нормализованная сложность
            complexity = (total_entities / 100) * (type_diversity / 5)
            
            return min(complexity, 1.0)
            
        except Exception as e:
            logger.warning(f"Ошибка оценки геометрической сложности: {e}")
            return 0.5
    
    def _assess_spatial_efficiency(self, features: Dict[str, Any]) -> float:
        """Оценка пространственной эффективности."""
        try:
            spatial_features = features.get("spatial_features", {})
            
            # Равномерность распределения
            distribution_evenness = spatial_features.get("distribution_evenness", 0)
            
            # Дисперсия центроидов
            centroid_x_std = spatial_features.get("centroid_x_std", 0)
            centroid_y_std = spatial_features.get("centroid_y_std", 0)
            
            # Оценка пространственной эффективности
            spatial_efficiency = (
                0.6 * distribution_evenness +
                0.2 * (1.0 - min(centroid_x_std / 1000, 1.0)) +
                0.2 * (1.0 - min(centroid_y_std / 1000, 1.0))
            )
            
            return max(0.0, min(1.0, spatial_efficiency))
            
        except Exception as e:
            logger.warning(f"Ошибка оценки пространственной эффективности: {e}")
            return 0.5
    
    def _assess_technical_feasibility(self, predictions: Dict[str, Any], 
                                    features: Dict[str, Any]) -> float:
        """Оценка технологической осуществимости."""
        try:
            feasibility_score = 1.0
            
            # Проверка параметров корректировки
            if "correction_params" in predictions:
                params = predictions["correction_params"]
                
                # Проверяем разумность перемещений
                if len(params) >= 2:
                    dx, dy = abs(params[0]), abs(params[1])
                    if dx > 100 or dy > 100:  # Слишком большие перемещения
                        feasibility_score *= 0.5
                
                # Проверяем разумность поворота
                if len(params) >= 3:
                    rotation = abs(params[2])
                    if rotation > 30:  # Слишком большой поворот
                        feasibility_score *= 0.7
            
            # Проверка типа корректировки
            if "correction_type" in predictions:
                correction_type = predictions["correction_type"]
                if correction_type == "custom":
                    feasibility_score *= 0.8  # Сложные корректировки менее осуществимы
            
            return feasibility_score
            
        except Exception as e:
            logger.warning(f"Ошибка оценки технологической осуществимости: {e}")
            return 0.5
    
    def _assess_economic_efficiency(self, predictions: Dict[str, Any], 
                                  features: Dict[str, Any]) -> float:
        """Оценка экономической эффективности."""
        try:
            economic_score = 1.0
            
            # Оценка потенциальной экономии материала
            if "improvement_potential" in predictions:
                improvement = predictions["improvement_potential"]
                material_savings = improvement * 0.15  # До 15% экономии материала
                economic_score *= (1.0 + material_savings)
            
            # Оценка экономии времени обработки
            optimization_features = features.get("optimization_features", {})
            cutting_efficiency = optimization_features.get("cutting_efficiency", 0)
            time_savings = cutting_efficiency * 0.1  # До 10% экономии времени
            economic_score *= (1.0 + time_savings)
            
            # Ограничиваем максимальный коэффициент
            return min(economic_score, 2.0)
            
        except Exception as e:
            logger.warning(f"Ошибка оценки экономической эффективности: {e}")
            return 1.0
    
    def _calculate_overall_score(self, prediction_metrics: Dict[str, float],
                               geometric_metrics: Dict[str, float],
                               optimization_metrics: Dict[str, float]) -> float:
        """Расчет общей оценки качества."""
        try:
            # Веса для разных типов метрик
            weights = {
                "prediction": 0.3,
                "geometric": 0.4,
                "optimization": 0.3
            }
            
            # Оценка предсказаний
            prediction_score = (
                prediction_metrics.get("params_reasonableness", 0) * 0.4 +
                prediction_metrics.get("confidence_reliability", 0) * 0.3 +
                prediction_metrics.get("correction_type_confidence", 0) * 0.3
            )
            
            # Оценка геометрии
            geometric_score = (
                geometric_metrics.get("improvement_potential", 0) * 0.4 +
                geometric_metrics.get("spatial_efficiency", 0) * 0.3 +
                (1.0 - geometric_metrics.get("geometric_complexity", 0)) * 0.3
            )
            
            # Оценка оптимизации
            optimization_score = optimization_metrics.get("overall_optimization_score", 0)
            
            # Общая оценка
            overall_score = (
                weights["prediction"] * prediction_score +
                weights["geometric"] * geometric_score +
                weights["optimization"] * optimization_score
            )
            
            return max(0.0, min(1.0, overall_score))
            
        except Exception as e:
            logger.warning(f"Ошибка расчета общей оценки: {e}")
            return 0.5
    
    def compare_with_baseline(self, baseline_metrics: Dict[str, float],
                            current_metrics: Dict[str, float]) -> Dict[str, float]:
        """Сравнение с базовым решением."""
        comparison = {}
        
        for metric_name in current_metrics:
            if metric_name in baseline_metrics:
                baseline_value = baseline_metrics[metric_name]
                current_value = current_metrics[metric_name]
                
                if baseline_value != 0:
                    improvement = (current_value - baseline_value) / baseline_value
                    comparison[f"{metric_name}_improvement"] = improvement
                else:
                    comparison[f"{metric_name}_improvement"] = 0.0
        
        return comparison
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик."""
        if not self.metrics_history:
            return {"message": "Нет данных для анализа"}
        
        summary = {
            "total_evaluations": len(self.metrics_history),
            "average_scores": {},
            "best_scores": {},
            "worst_scores": {},
            "trends": {}
        }
        
        # Анализ по каждой метрике
        metric_names = set()
        for metrics in self.metrics_history:
            metric_names.update(metrics.keys())
        
        for metric_name in metric_names:
            values = [m.get(metric_name, 0) for m in self.metrics_history]
            if values:
                summary["average_scores"][metric_name] = np.mean(values)
                summary["best_scores"][metric_name] = np.max(values)
                summary["worst_scores"][metric_name] = np.min(values)
                
                # Анализ тренда
                if len(values) > 1:
                    trend = np.polyfit(range(len(values)), values, 1)[0]
                    summary["trends"][metric_name] = trend
        
        return summary
    
    def _get_default_metrics(self) -> Dict[str, float]:
        """Дефолтные метрики при ошибке."""
        return {
            "params_reasonableness": 0.5,
            "confidence_reliability": 0.5,
            "correction_type_confidence": 0.5,
            "improvement_potential": 0.0,
            "spatial_efficiency": 0.5,
            "geometric_complexity": 0.5,
            "technical_feasibility": 0.5,
            "economic_efficiency": 1.0,
            "overall_optimization_score": 0.5,
            "overall_score": 0.5
        } 