"""
Модуль для работы с остатками материала.

Обеспечивает извлечение признаков остатков, оценку их пригодности
для новых заказов и предсказание форм новых остатков.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Leftover:
    """Структура для представления остатка материала."""

    id: str
    geometry: Any  # Shapely Polygon в реальной реализации
    material_code: str
    thickness: float
    creation_date: str
    source_dxf: str  # из какого DXF получен
    usage_count: int = 0  # сколько раз использовался
    priority: float = 1.0  # приоритет использования
    area: float = 0.0  # площадь остатка
    width: float = 0.0  # ширина
    height: float = 0.0  # высота


class LeftoverFeatureExtractor:
    """Извлечение признаков для работы с остатками."""

    def __init__(self):
        self.leftovers_db: List[Leftover] = []
        self.minimum_leftover_area = 5000  # 50 см²
        self.compatibility_threshold = 0.5

    def extract_leftover_features(
        self, dxf_data: Dict, available_leftovers: List[Leftover]
    ) -> Dict[str, Any]:
        """Извлечь признаки, связанные с остатками."""
        try:
            return {
                "material_efficiency": self._calculate_material_efficiency(
                    dxf_data, available_leftovers
                ),
                "leftover_suitability": self._evaluate_leftover_suitability(
                    dxf_data, available_leftovers
                ),
                "new_leftovers_potential": self._predict_new_leftovers(
                    dxf_data
                ),
                "optimization_strategy": self._determine_optimization_strategy(
                    dxf_data, available_leftovers
                ),
            }
        except Exception as e:
            logger.error(f"Error extracting leftover features: {e}")
            return self._get_default_features()

    def _calculate_material_efficiency(
        self, dxf_data: Dict, leftovers: List[Leftover]
    ) -> Dict[str, Any]:
        """Оценка эффективности использования материала с учетом остатков."""
        try:
            # Общая площадь заказа
            order_area = sum(
                self._get_entity_area(e) for e in dxf_data.get("entities", [])
            )

            # Площадь, которая может быть покрыта остатками
            leftover_coverage = 0
            suitable_leftovers = []

            for leftover in leftovers:
                compatibility_score = self._calculate_compatibility(
                    dxf_data, leftover
                )
                if compatibility_score > self.compatibility_threshold:
                    suitable_leftovers.append(leftover)
                    leftover_coverage += leftover.area

            # Эффективность использования остатков
            coverage_ratio = (
                leftover_coverage / order_area if order_area > 0 else 0
            )

            return {
                "total_leftover_area_available": sum(
                    l.area for l in leftovers
                ),
                "suitable_leftovers_count": len(suitable_leftovers),
                "leftover_coverage_ratio": coverage_ratio,
                "material_savings_potential": coverage_ratio
                * 100,  # в процентах
                "new_sheet_required": coverage_ratio
                < 0.8,  # нужны новые листы
                "suitable_leftovers": suitable_leftovers,
            }
        except Exception as e:
            logger.error(f"Error calculating material efficiency: {e}")
            return self._get_default_material_efficiency()

    def _evaluate_leftover_suitability(
        self, dxf_data: Dict, leftovers: List[Leftover]
    ) -> List[Dict[str, Any]]:
        """Оценка пригодности каждого остатка для текущего заказа."""
        try:
            order_pieces = self._extract_order_pieces(dxf_data)
            suitable_leftovers = []

            for leftover in leftovers:
                # Базовая проверка по материалу и толщине
                if not self._matches_material_spec(dxf_data, leftover):
                    continue

                # Геометрическая оценка
                geometric_score = self._calculate_geometric_suitability(
                    order_pieces, leftover
                )

                # Оценка по возрасту и частоте использования
                recency_score = self._calculate_recency_score(leftover)
                usage_score = self._calculate_usage_score(leftover)

                # Комбинированная оценка пригодности
                total_score = (
                    0.6 * geometric_score
                    + 0.2 * recency_score
                    + 0.2 * usage_score
                )

                if total_score > 0.3:  # Минимальный порог
                    suitable_leftovers.append(
                        {
                            "leftover_id": leftover.id,
                            "suitability_score": total_score,
                            "geometric_score": geometric_score,
                            "recency_score": recency_score,
                            "usage_score": usage_score,
                            "optimization_potential": self._estimate_optimization_potential(
                                order_pieces, leftover
                            ),
                            "area": leftover.area,
                            "material_code": leftover.material_code,
                        }
                    )

            # Сортировка по пригодности
            suitable_leftovers.sort(
                key=lambda x: x["suitability_score"], reverse=True
            )
            return suitable_leftovers
        except Exception as e:
            logger.error(f"Error evaluating leftover suitability: {e}")
            return []

    def _predict_new_leftovers(self, dxf_data: Dict) -> List[Dict[str, Any]]:
        """Предсказание новых остатков, которые будут получены после раскроя."""
        try:
            # Анализ текущей карты и предсказание форм остатков
            sheet_polygons = self._extract_sheet_polygons(dxf_data)
            pieces = self._extract_piece_polygons(dxf_data)

            predicted_leftovers = []

            for sheet in sheet_polygons:
                # Упрощенная модель - вычитаем площадь деталей из листа
                sheet_area = sheet.get("area", 100000)  # 1м² по умолчанию
                pieces_area = sum(p.get("area", 0) for p in pieces)

                remaining_area = max(0, sheet_area - pieces_area)

                if remaining_area > self.minimum_leftover_area:
                    # Предсказание формы остатка
                    leftover_shape = self._predict_leftover_shape(
                        sheet, pieces, remaining_area
                    )

                    predicted_leftovers.append(
                        {
                            "geometry": leftover_shape,
                            "area": remaining_area,
                            "bounding_box": self._calculate_bounding_box(
                                leftover_shape
                            ),
                            "utilization_potential": self._calculate_utilization_potential(
                                remaining_area
                            ),
                            "storage_efficiency": self._calculate_storage_efficiency(
                                leftover_shape
                            ),
                            "priority": self._calculate_priority(
                                remaining_area, leftover_shape
                            ),
                        }
                    )

            # Сортировка по приоритету
            predicted_leftovers.sort(
                key=lambda x: x["utilization_potential"], reverse=True
            )
            return predicted_leftovers
        except Exception as e:
            logger.error(f"Error predicting new leftovers: {e}")
            return []

    def _determine_optimization_strategy(
        self, dxf_data: Dict, leftovers: List[Leftover]
    ) -> Dict[str, Any]:
        """Определение стратегии оптимизации на основе доступных остатков."""
        try:
            # Анализ состава заказа
            entities = dxf_data.get("entities", [])
            has_large_pieces = any(
                self._get_entity_area(e) > 100000 for e in entities
            )
            has_small_pieces = any(
                self._get_entity_area(e) < 10000 for e in entities
            )

            # Анализ остатков
            large_leftovers = [l for l in leftovers if l.area > 50000]
            small_leftovers = [l for l in leftovers if l.area <= 50000]

            # Определение стратегии
            strategy = {
                "primary_strategy": "mixed",  # смешанная
                "leftover_first": len(large_leftovers)
                > 0,  # приоритет остаткам
                "minimize_new_sheets": True,
                "optimize_for_future_use": True,
                "large_pieces_present": has_large_pieces,
                "small_pieces_present": has_small_pieces,
            }

            # Корректировка стратегии на основе анализа
            if has_large_pieces and len(large_leftovers) == 0:
                strategy["primary_strategy"] = (
                    "new_sheets"  # нужны новые листы
                )
            elif has_small_pieces and len(small_leftovers) > 3:
                strategy["primary_strategy"] = (
                    "leftover_efficient"  # эффективное использование остатков
                )

            return strategy
        except Exception as e:
            logger.error(f"Error determining optimization strategy: {e}")
            return {"primary_strategy": "mixed", "leftover_first": False}

    def _calculate_compatibility(
        self, dxf_data: Dict, leftover: Leftover
    ) -> float:
        """Расчет совместимости остатка с заказом."""
        try:
            # Пространственная оценка - может ли остаток вместить детали
            entities = dxf_data.get("entities", [])
            if not entities:
                return 0.0

            max_piece_width = max(self._get_entity_width(e) for e in entities)
            max_piece_height = max(
                self._get_entity_height(e) for e in entities
            )

            # Базовая пространственная совместимость
            spatial_fit = min(
                leftover.width / max_piece_width if max_piece_width > 0 else 1,
                (
                    leftover.height / max_piece_height
                    if max_piece_height > 0
                    else 1
                ),
            )

            # Ограничиваем сверху 1.0
            return min(spatial_fit, 1.0)
        except Exception as e:
            logger.error(f"Error calculating compatibility: {e}")
            return 0.0

    def _calculate_geometric_suitability(
        self, order_pieces: List, leftover: Leftover
    ) -> float:
        """Расчет геометрической пригодности остатка."""
        try:
            total_pieces_area = sum(p.get("area", 0) for p in order_pieces)
            leftover_area = leftover.area

            # Идеальное соотношение
            if total_pieces_area <= leftover_area:
                return 1.0

            # Частичное использование
            coverage = leftover_area / total_pieces_area
            return coverage * 0.7  # штраф за неполное использование
        except Exception as e:
            logger.error(f"Error calculating geometric suitability: {e}")
            return 0.0

    def _calculate_recency_score(self, leftover: Leftover) -> float:
        """Расчет оценки по возрасту остатка."""
        try:
            # Чем новее остаток, тем выше приоритет
            creation_date = datetime.fromisoformat(
                leftover.creation_date.replace("Z", "+00:00")
            )
            days_old = (datetime.now() - creation_date).days

            # Экспоненциальное затухание
            recency_score = np.exp(
                -days_old / 30
            )  # 30 дней - период полураспада
            return recency_score
        except Exception as e:
            logger.error(f"Error calculating recency score: {e}")
            return 0.5

    def _calculate_usage_score(self, leftover: Leftover) -> float:
        """Расчет оценки по частоте использования."""
        try:
            # Чем меньше использовался, тем выше приоритет
            usage_score = 1.0 / (1.0 + leftover.usage_count)
            return usage_score
        except Exception as e:
            logger.error(f"Error calculating usage score: {e}")
            return 0.5

    def _estimate_optimization_potential(
        self, order_pieces: List, leftover: Leftover
    ) -> float:
        """Оценка потенциала оптимизации для данного остатка."""
        try:
            # Упрощенная оценка на основе площади и формы
            area_ratio = leftover.area / sum(
                p.get("area", 0) for p in order_pieces
            )
            aspect_ratio = (
                leftover.width / leftover.height if leftover.height > 0 else 1
            )

            # Идеальная форма - квадрат
            form_factor = 1.0 - abs(1.0 - aspect_ratio) * 0.3

            return min(area_ratio * form_factor, 1.0)
        except Exception as e:
            logger.error(f"Error estimating optimization potential: {e}")
            return 0.5

    def _predict_leftover_shape(
        self, sheet: Dict, pieces: List, remaining_area: float
    ) -> Dict[str, Any]:
        """Предсказание формы остатка."""
        try:
            # Упрощенная модель - прямоугольный остаток
            sheet_width = sheet.get("width", 1000)

            # Предполагаем, что остаток будет в углу листа
            leftover_width = min(sheet_width, np.sqrt(remaining_area * 2))
            leftover_height = remaining_area / leftover_width

            return {
                "type": "rectangle",
                "width": leftover_width,
                "height": leftover_height,
                "area": remaining_area,
            }
        except Exception as e:
            logger.error(f"Error predicting leftover shape: {e}")
            return {"type": "unknown", "area": remaining_area}

    def _calculate_bounding_box(
        self, shape: Dict
    ) -> Tuple[float, float, float, float]:
        """Расчет ограничивающего прямоугольника."""
        try:
            if shape.get("type") == "rectangle":
                width = shape.get("width", 0)
                height = shape.get("height", 0)
                return (0, 0, width, height)
            else:
                return (0, 0, 100, 100)  # значения по умолчанию
        except Exception as e:
            logger.error(f"Error calculating bounding box: {e}")
            return (0, 0, 100, 100)

    def _calculate_utilization_potential(self, area: float) -> float:
        """Расчет потенциала использования остатка."""
        try:
            # Большие остатки имеют больший потенциал
            if area > 50000:  # > 0.5м²
                return 0.9
            elif area > 20000:  # > 0.2м²
                return 0.7
            elif area > 10000:  # > 0.1м²
                return 0.5
            else:
                return 0.3
        except Exception as e:
            logger.error(f"Error calculating utilization potential: {e}")
            return 0.5

    def _calculate_storage_efficiency(self, shape: Dict) -> float:
        """Расчет эффективности хранения остатка."""
        try:
            # Прямоугольные остатки легче хранить
            if shape.get("type") == "rectangle":
                width = shape.get("width", 0)
                height = shape.get("height", 0)
                aspect_ratio = width / height if height > 0 else 1

                # Оптимальное соотношение сторон для хранения
                if 0.5 <= aspect_ratio <= 2.0:
                    return 0.9
                else:
                    return 0.6
            else:
                return 0.5
        except Exception as e:
            logger.error(f"Error calculating storage efficiency: {e}")
            return 0.5

    def _calculate_priority(self, area: float, shape: Dict) -> float:
        """Расчет приоритета остатка."""
        try:
            utilization = self._calculate_utilization_potential(area)
            storage = self._calculate_storage_efficiency(shape)

            return (utilization + storage) / 2
        except Exception as e:
            logger.error(f"Error calculating priority: {e}")
            return 0.5

    # Вспомогательные методы
    def _get_entity_area(self, entity: Dict) -> float:
        """Получение площади сущности."""
        return entity.get("area", 0)

    def _get_entity_width(self, entity: Dict) -> float:
        """Получение ширины сущности."""
        return entity.get("width", 0)

    def _get_entity_height(self, entity: Dict) -> float:
        """Получение высоты сущности."""
        return entity.get("height", 0)

    def _extract_order_pieces(self, dxf_data: Dict) -> List[Dict]:
        """Извлечение деталей заказа."""
        return dxf_data.get("entities", [])

    def _extract_sheet_polygons(self, dxf_data: Dict) -> List[Dict]:
        """Извлечение полигонов листов."""
        return dxf_data.get("sheets", [])

    def _extract_piece_polygons(self, dxf_data: Dict) -> List[Dict]:
        """Извлечение полигонов деталей."""
        return dxf_data.get("entities", [])

    def _matches_material_spec(
        self, dxf_data: Dict, leftover: Leftover
    ) -> bool:
        """Проверка соответствия спецификации материала."""
        order_material = dxf_data.get("material_code", "MDF")
        order_thickness = dxf_data.get("thickness", 16.0)

        return (
            leftover.material_code == order_material
            and abs(leftover.thickness - order_thickness) < 0.1
        )

    def _get_default_features(self) -> Dict[str, Any]:
        """Получение признаков по умолчанию."""
        return {
            "material_efficiency": self._get_default_material_efficiency(),
            "leftover_suitability": [],
            "new_leftovers_potential": [],
            "optimization_strategy": {
                "primary_strategy": "mixed",
                "leftover_first": False,
            },
        }

    def _get_default_material_efficiency(self) -> Dict[str, Any]:
        """Получение эффективности материала по умолчанию."""
        return {
            "total_leftover_area_available": 0,
            "suitable_leftovers_count": 0,
            "leftover_coverage_ratio": 0,
            "material_savings_potential": 0,
            "new_sheet_required": True,
            "suitable_leftovers": [],
        }
