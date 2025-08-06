"""
Оптимизатор для работы с остатками материала.

Обеспечивает оптимальное назначение деталей на остатки,
оценку совместимости и предсказание новых остатков.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import logging
from datetime import datetime

from ..features.leftovers import Leftover

logger = logging.getLogger(__name__)


@dataclass
class LeftoverAssignment:
    """Назначение детали на остаток."""
    piece_id: str
    leftover_id: str
    position: Tuple[float, float]
    rotation: float
    confidence: float
    area_utilization: float


class LeftoverOptimizationModel(nn.Module):
    """Модель для оптимизации использования остатков."""
    
    def __init__(self, feature_dim: int = 256, num_leftover_types: int = 10):
        super().__init__()
        
        # Энкодер характеристик остатка
        self.leftover_encoder = nn.Sequential(
            nn.Linear(feature_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        # Энкодер характеристик детали
        self.piece_encoder = nn.Sequential(
            nn.Linear(feature_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        # Сеть для оценки совместимости
        self.compatibility_network = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        # Сеть для предсказания оптимального размещения
        self.placement_network = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 3),  # x, y, rotation
            nn.Tanh()
        )
        
        # Классификатор типа оптимизации
        self.strategy_classifier = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, num_leftover_types),
            nn.Softmax(dim=-1)
        )
        
        # Сеть для оценки эффективности использования
        self.efficiency_network = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, leftover_features: torch.Tensor, piece_features: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Прямой проход модели."""
        # Кодирование характеристик
        leftover_encoded = self.leftover_encoder(leftover_features)
        piece_encoded = self.piece_encoder(piece_features)
        
        # Объединение признаков
        combined = torch.cat([leftover_encoded, piece_encoded], dim=-1)
        
        # Оценка совместимости
        compatibility = self.compatibility_network(combined)
        
        # Предсказание размещения
        placement = self.placement_network(combined)
        placement = placement * 100  # масштабирование координат
        
        # Классификация стратегии
        strategy = self.strategy_classifier(combined)
        
        # Оценка эффективности
        efficiency = self.efficiency_network(combined)
        
        return {
            "compatibility": compatibility,
            "placement": placement,
            "strategy": strategy,
            "efficiency": efficiency
        }


class LeftoverOptimizer:
    """Оптимизатор для работы с остатками."""
    
    def __init__(self, model: LeftoverOptimizationModel, config: Dict[str, Any]):
        self.model = model
        self.config = config
        self.device = torch.device(config.get("device", "cuda" if torch.cuda.is_available() else "cpu"))
        self.model.to(self.device)
        self.model.eval()
        
        # Параметры оптимизации
        self.min_compatibility_threshold = config.get("min_compatibility", 0.5)
        self.max_iterations = config.get("max_iterations", 100)
        self.convergence_threshold = config.get("convergence_threshold", 1e-4)
    
    def optimize_layout(self, dxf_data: Dict, available_leftovers: List[Leftover]) -> Dict[str, Any]:
        """Оптимизация раскладки с использованием остатков."""
        try:
            start_time = datetime.now()
            
            # 1. Извлечение признаков деталей
            pieces = self._extract_pieces_features(dxf_data)
            
            # 2. Извлечение признаков остатков
            leftover_features = self._extract_leftovers_features(available_leftovers)
            
            # 3. Поиск оптимальных назначений
            assignments = self._find_optimal_assignments(pieces, leftover_features)
            
            # 4. Расчет новых остатков
            new_leftovers = self._predict_new_leftovers(dxf_data, assignments)
            
            # 5. Оценка эффективности
            efficiency_metrics = self._calculate_efficiency_metrics(
                dxf_data, assignments, new_leftovers
            )
            
            # 6. Формирование оптимизированной раскладки
            optimized_layout = self._generate_optimized_layout(assignments, dxf_data)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "assignments": assignments,
                "optimized_layout": optimized_layout,
                "new_leftovers": new_leftovers,
                "efficiency_metrics": efficiency_metrics,
                "strategy_used": self._determine_strategy(efficiency_metrics),
                "processing_time_ms": int(processing_time * 1000),
                "iterations_performed": len(assignments)
            }
            
        except Exception as e:
            logger.error(f"Error in leftover optimization: {e}")
            return {
                "assignments": [],
                "optimized_layout": {},
                "new_leftovers": [],
                "efficiency_metrics": self._get_default_efficiency_metrics(),
                "strategy_used": "fallback",
                "error": str(e)
            }
    
    def _extract_pieces_features(self, dxf_data: Dict) -> List[Dict]:
        """Извлечение признаков деталей."""
        pieces = []
        entities = dxf_data.get("entities", [])
        
        for i, entity in enumerate(entities):
            piece_features = {
                "id": f"piece_{i}",
                "area": entity.get("area", 0),
                "width": entity.get("width", 0),
                "height": entity.get("height", 0),
                "perimeter": entity.get("perimeter", 0),
                "aspect_ratio": entity.get("aspect_ratio", 1.0),
                "complexity": entity.get("complexity", 1.0),
                "features": self._create_piece_feature_vector(entity)
            }
            pieces.append(piece_features)
        
        return pieces
    
    def _extract_leftovers_features(self, leftovers: List[Leftover]) -> List[Dict]:
        """Извлечение признаков остатков."""
        leftover_features = []
        
        for leftover in leftovers:
            features = {
                "id": leftover.id,
                "area": leftover.area,
                "width": leftover.width,
                "height": leftover.height,
                "aspect_ratio": leftover.width / leftover.height if leftover.height > 0 else 1.0,
                "usage_count": leftover.usage_count,
                "priority": leftover.priority,
                "material_code": leftover.material_code,
                "thickness": leftover.thickness,
                "features": self._create_leftover_feature_vector(leftover)
            }
            leftover_features.append(features)
        
        return leftover_features
    
    def _find_optimal_assignments(self, pieces: List[Dict], leftovers_features: List[Dict]) -> List[LeftoverAssignment]:
        """Поиск оптимального назначения деталей на остатки."""
        assignments = []
        used_pieces = set()
        used_leftovers = set()
        
        # Сортировка деталей по площади (убывание) - большие детали приоритетнее
        sorted_pieces = sorted(pieces, key=lambda x: x["area"], reverse=True)
        
        for piece in sorted_pieces:
            if piece["id"] in used_pieces:
                continue
            
            best_assignment = None
            best_score = 0
            
            # Поиск лучшего остатка для детали
            for leftover in leftovers_features:
                if leftover["id"] in used_leftovers:
                    continue
                
                # Подготовка данных для модели
                piece_tensor = torch.FloatTensor(piece["features"]).unsqueeze(0).to(self.device)
                leftover_tensor = torch.FloatTensor(leftover["features"]).unsqueeze(0).to(self.device)
                
                # Предсказание модели
                with torch.no_grad():
                    predictions = self.model(leftover_tensor, piece_tensor)
                    compatibility = predictions["compatibility"].item()
                    placement = predictions["placement"].cpu().numpy()[0]
                    efficiency = predictions["efficiency"].item()
                
                # Комбинированная оценка
                combined_score = (
                    0.6 * compatibility +
                    0.3 * efficiency +
                    0.1 * leftover["priority"]
                )
                
                # Обновление лучшего варианта
                if combined_score > best_score and compatibility > self.min_compatibility_threshold:
                    best_score = combined_score
                    best_assignment = LeftoverAssignment(
                        piece_id=piece["id"],
                        leftover_id=leftover["id"],
                        position=(placement[0], placement[1]),
                        rotation=placement[2],
                        confidence=compatibility,
                        area_utilization=efficiency
                    )
            
            # Сохранение лучшего назначения
            if best_assignment:
                assignments.append(best_assignment)
                used_pieces.add(piece["id"])
                used_leftovers.add(best_assignment.leftover_id)
        
        return assignments
    
    def _predict_new_leftovers(self, dxf_data: Dict, assignments: List[LeftoverAssignment]) -> List[Dict[str, Any]]:
        """Предсказание новых остатков после раскроя."""
        new_leftovers = []
        
        # Группировка назначений по остаткам
        assignments_by_leftover = {}
        for assignment in assignments:
            leftover_id = assignment.leftover_id
            if leftover_id not in assignments_by_leftover:
                assignments_by_leftover[leftover_id] = []
            assignments_by_leftover[leftover_id].append(assignment)
        
        # Для каждого задействованного остатка
        for leftover_id, leftover_assignments in assignments_by_leftover.items():
            # Расчет оставшейся площади
            total_assigned_area = sum(
                self._get_piece_area_by_id(assignment.piece_id, dxf_data) 
                for assignment in leftover_assignments
            )
            
            # Получаем информацию об остатке
            leftover_info = self._get_leftover_info(leftover_id)
            if leftover_info:
                remaining_area = max(0, leftover_info["area"] - total_assigned_area)
                
                if remaining_area > 5000:  # Минимальная площадь для сохранения
                    new_leftover = {
                        "source_leftover_id": leftover_id,
                        "area_remaining": remaining_area,
                        "geometry_type": "irregular",
                        "reuse_priority": self._calculate_reuse_priority(remaining_area),
                        "creation_date": datetime.now().isoformat(),
                        "material_code": leftover_info.get("material_code", "MDF"),
                        "thickness": leftover_info.get("thickness", 16.0)
                    }
                    new_leftovers.append(new_leftover)
        
        return new_leftovers
    
    def _calculate_efficiency_metrics(self, dxf_data: Dict, assignments: List[LeftoverAssignment], 
                                   new_leftovers: List[Dict]) -> Dict[str, float]:
        """Расчет метрик эффективности использования остатков."""
        try:
            # Общая площадь заказа
            total_piece_area = sum(self._get_piece_area_by_id(p["id"], dxf_data) 
                                 for p in self._extract_pieces_features(dxf_data))
            
            # Площадь, закрытая остатками
            leftover_area_covered = sum(
                self._get_piece_area_by_id(assignment.piece_id, dxf_data) * assignment.area_utilization
                for assignment in assignments
            )
            
            # Потенциальная экономия
            potential_savings = leftover_area_covered / total_piece_area if total_piece_area > 0 else 0
            
            # Эффективность новых остатков
            avg_leftover_reuse = np.mean([l.get("reuse_priority", 0) for l in new_leftovers]) if new_leftovers else 0
            
            # Дополнительные метрики
            assignment_efficiency = np.mean([a.area_utilization for a in assignments]) if assignments else 0
            coverage_ratio = len(assignments) / len(self._extract_pieces_features(dxf_data)) if dxf_data.get("entities") else 0
            
            return {
                "material_efficiency": potential_savings,
                "leftover_utilization_rate": coverage_ratio,
                "new_leftovers_quality": avg_leftover_reuse,
                "assignment_efficiency": assignment_efficiency,
                "overall_score": (potential_savings + avg_leftover_reuse + assignment_efficiency) / 3,
                "pieces_assigned": len(assignments),
                "total_pieces": len(self._extract_pieces_features(dxf_data))
            }
        except Exception as e:
            logger.error(f"Error calculating efficiency metrics: {e}")
            return self._get_default_efficiency_metrics()
    
    def _generate_optimized_layout(self, assignments: List[LeftoverAssignment], dxf_data: Dict) -> Dict[str, Any]:
        """Генерация оптимизированной раскладки."""
        try:
            layout = {
                "assignments": [],
                "total_area_utilized": 0,
                "leftovers_used": set(),
                "pieces_placed": set()
            }
            
            for assignment in assignments:
                piece_info = self._get_piece_info(assignment.piece_id, dxf_data)
                leftover_info = self._get_leftover_info(assignment.leftover_id)
                
                if piece_info and leftover_info:
                    layout["assignments"].append({
                        "piece_id": assignment.piece_id,
                        "leftover_id": assignment.leftover_id,
                        "position": assignment.position,
                        "rotation": assignment.rotation,
                        "confidence": assignment.confidence,
                        "area_utilization": assignment.area_utilization,
                        "piece_area": piece_info.get("area", 0),
                        "leftover_area": leftover_info.get("area", 0)
                    })
                    
                    layout["total_area_utilized"] += piece_info.get("area", 0) * assignment.area_utilization
                    layout["leftovers_used"].add(assignment.leftover_id)
                    layout["pieces_placed"].add(assignment.piece_id)
            
            layout["leftovers_used"] = list(layout["leftovers_used"])
            layout["pieces_placed"] = list(layout["pieces_placed"])
            
            return layout
            
        except Exception as e:
            logger.error(f"Error generating optimized layout: {e}")
            return {"assignments": [], "total_area_utilized": 0}
    
    def _determine_strategy(self, efficiency_metrics: Dict[str, float]) -> str:
        """Определение использованной стратегии."""
        material_efficiency = efficiency_metrics.get("material_efficiency", 0)
        leftover_utilization = efficiency_metrics.get("leftover_utilization_rate", 0)
        
        if material_efficiency > 0.7 and leftover_utilization > 0.8:
            return "high_efficiency_leftover_optimization"
        elif material_efficiency > 0.5:
            return "moderate_leftover_optimization"
        elif leftover_utilization > 0.3:
            return "basic_leftover_usage"
        else:
            return "new_sheets_required"
    
    # Вспомогательные методы
    def _create_piece_feature_vector(self, entity: Dict) -> List[float]:
        """Создание вектора признаков детали."""
        return [
            entity.get("area", 0) / 100000,  # нормализованная площадь
            entity.get("width", 0) / 1000,   # нормализованная ширина
            entity.get("height", 0) / 1000,  # нормализованная высота
            entity.get("perimeter", 0) / 1000,  # нормализованный периметр
            entity.get("aspect_ratio", 1.0),
            entity.get("complexity", 1.0),
            # Дополнительные признаки
            *[0.0] * 250  # заполнение до 256 признаков
        ]
    
    def _create_leftover_feature_vector(self, leftover: Leftover) -> List[float]:
        """Создание вектора признаков остатка."""
        return [
            leftover.area / 100000,  # нормализованная площадь
            leftover.width / 1000,   # нормализованная ширина
            leftover.height / 1000,  # нормализованная высота
            leftover.usage_count / 10,  # нормализованное количество использований
            leftover.priority,
            leftover.thickness / 20,  # нормализованная толщина
            # Кодирование материала
            1.0 if leftover.material_code == "MDF" else 0.0,
            1.0 if leftover.material_code == "ДСП" else 0.0,
            1.0 if leftover.material_code == "фанера" else 0.0,
            # Дополнительные признаки
            *[0.0] * 247  # заполнение до 256 признаков
        ]
    
    def _get_piece_area_by_id(self, piece_id: str, dxf_data: Dict) -> float:
        """Получение площади детали по ID."""
        pieces = self._extract_pieces_features(dxf_data)
        for piece in pieces:
            if piece["id"] == piece_id:
                return piece["area"]
        return 0.0
    
    def _get_piece_info(self, piece_id: str, dxf_data: Dict) -> Optional[Dict]:
        """Получение информации о детали по ID."""
        pieces = self._extract_pieces_features(dxf_data)
        for piece in pieces:
            if piece["id"] == piece_id:
                return piece
        return None
    
    def _get_leftover_info(self, leftover_id: str) -> Optional[Dict]:
        """Получение информации об остатке по ID."""
        # В реальной реализации это будет запрос к базе данных
        # Здесь возвращаем заглушку
        return {
            "area": 50000,  # 0.5м²
            "material_code": "MDF",
            "thickness": 16.0
        }
    
    def _calculate_reuse_priority(self, area: float) -> float:
        """Расчет приоритета повторного использования остатка."""
        if area > 50000:  # > 0.5м²
            return 0.9
        elif area > 20000:  # > 0.2м²
            return 0.7
        elif area > 10000:  # > 0.1м²
            return 0.5
        else:
            return 0.3
    
    def _get_default_efficiency_metrics(self) -> Dict[str, float]:
        """Получение метрик эффективности по умолчанию."""
        return {
            "material_efficiency": 0.0,
            "leftover_utilization_rate": 0.0,
            "new_leftovers_quality": 0.0,
            "assignment_efficiency": 0.0,
            "overall_score": 0.0,
            "pieces_assigned": 0,
            "total_pieces": 0
        } 