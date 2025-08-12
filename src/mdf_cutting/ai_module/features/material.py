"""
Извлечение признаков материалов.

Этот модуль содержит:
- Характеристики материалов
- Технологические параметры
- Свойства обработки
"""

import logging
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


class MaterialFeatureExtractor:
    """Извлечение признаков, связанных с материалами"""

    def __init__(self):
        """Инициализация экстрактора признаков материалов."""
        # Справочник материалов с характеристиками
        self.material_properties = {
            "MDF": {
                "density": 750,  # кг/м³
                "hardness": 0.7,  # относительная твердость
                "cutting_speed": 1.0,  # относительная скорость резки
                "surface_quality": 0.8,  # качество поверхности
                "moisture_resistance": 0.6,  # влагостойкость
                "cost_factor": 1.0,  # фактор стоимости
                "thickness_range": [3, 40],  # мм
                "standard_sizes": [
                    (2440, 1220),
                    (2800, 2070),
                    (3660, 1830),
                ],  # мм
            },
            "HDF": {
                "density": 850,
                "hardness": 0.9,
                "cutting_speed": 0.8,
                "surface_quality": 0.9,
                "moisture_resistance": 0.7,
                "cost_factor": 1.3,
                "thickness_range": [3, 25],
                "standard_sizes": [(2440, 1220), (2800, 2070)],
            },
            "ДСП": {
                "density": 650,
                "hardness": 0.5,
                "cutting_speed": 1.2,
                "surface_quality": 0.6,
                "moisture_resistance": 0.4,
                "cost_factor": 0.7,
                "thickness_range": [8, 40],
                "standard_sizes": [(2440, 1220), (2750, 1830)],
            },
            "фанера": {
                "density": 600,
                "hardness": 0.6,
                "cutting_speed": 1.1,
                "surface_quality": 0.7,
                "moisture_resistance": 0.8,
                "cost_factor": 1.5,
                "thickness_range": [3, 30],
                "standard_sizes": [(2440, 1220), (3050, 1525)],
            },
            "массив": {
                "density": 500,
                "hardness": 0.8,
                "cutning_speed": 0.9,
                "surface_quality": 0.9,
                "moisture_resistance": 0.5,
                "cost_factor": 2.0,
                "thickness_range": [10, 50],
                "standard_sizes": [(2000, 1000), (3000, 1500)],
            },
        }

        # Технологические параметры резки
        self.cutting_parameters = {
            "feed_rate": 5000,  # мм/мин - скорость подачи
            "spindle_speed": 18000,  # об/мин - скорость шпинделя
            "tool_diameter": 6.35,  # мм - диаметр инструмента
            "kerf_width": 3.2,  # мм - ширина реза
            "min_cut_length": 5,  # мм - минимальная длина реза
            "safety_margin": 2.0,  # мм - безопасный отступ
        }

    def extract_features(
        self, material_data: Dict, order_data: Dict
    ) -> Dict[str, Any]:
        """
        Извлечь признаки материалов.

        Args:
            material_data: Данные о материале
            order_data: Данные заказа

        Returns:
            Dict: Словарь с признаками материалов
        """
        try:
            basic_features = self._extract_basic_features(
                material_data, order_data
            )
            technical_features = self._extract_technical_features(
                material_data, order_data
            )
            processing_features = self._extract_processing_features(
                material_data, order_data
            )

            return {
                **basic_features,
                **technical_features,
                **processing_features,
            }
        except Exception as e:
            logger.error(f"Ошибка извлечения признаков материалов: {e}")
            return self._get_default_material_features()

    def _extract_basic_features(
        self, material_data: Dict, order_data: Dict
    ) -> Dict:
        """Базовые признаки материала."""
        material_type = material_data.get(
            "type", order_data.get("material_code", "MDF")
        )
        thickness = material_data.get(
            "thickness", order_data.get("thickness", 16.0)
        )
        quantity = order_data.get("quantity", 1)

        # Получаем свойства материала
        properties = self.material_properties.get(
            material_type.upper(), self.material_properties["MDF"]
        )

        # Размеры листа
        sheet_size = self._get_sheet_size(material_type, material_data)

        return {
            "material_type": material_type,
            "material_thickness": thickness,
            "material_density": properties["density"],
            "material_hardness": properties["hardness"],
            "material_cost_factor": properties["cost_factor"],
            "sheet_width": sheet_size[0],
            "sheet_height": sheet_size[1],
            "sheet_area": sheet_size[0] * sheet_size[1],
            "order_quantity": quantity,
            "total_material_area": sheet_size[0] * sheet_size[1] * quantity,
            "is_standard_thickness": self._is_standard_thickness(
                thickness, material_type
            ),
            "is_standard_size": self._is_standard_size(
                sheet_size, material_type
            ),
        }

    def _extract_technical_features(
        self, material_data: Dict, order_data: Dict
    ) -> Dict:
        """Технические характеристики материала."""
        material_type = material_data.get(
            "type", order_data.get("material_code", "MDF")
        )
        thickness = material_data.get(
            "thickness", order_data.get("thickness", 16.0)
        )

        properties = self.material_properties.get(
            material_type.upper(), self.material_properties["MDF"]
        )

        # Расчет массы и объема
        sheet_size = self._get_sheet_size(material_type, material_data)
        sheet_area = sheet_size[0] * sheet_size[1]
        sheet_volume = sheet_area * thickness / 1000000  # м³
        sheet_weight = sheet_volume * properties["density"]

        # Технологические характеристики
        cutting_speed_factor = properties["cutting_speed"]
        surface_quality = properties["surface_quality"]
        moisture_resistance = properties["moisture_resistance"]

        return {
            "sheet_volume_m3": sheet_volume,
            "sheet_weight_kg": sheet_weight,
            "cutting_speed_factor": cutting_speed_factor,
            "surface_quality": surface_quality,
            "moisture_resistance": moisture_resistance,
            "thickness_factor": thickness
            / 16.0,  # относительно стандартной толщины
            "density_factor": properties["density"]
            / 750.0,  # относительно МДФ
            "hardness_factor": properties["hardness"],
            "material_strength": self._calculate_material_strength(
                properties, thickness
            ),
            "cutting_difficulty": self._calculate_cutting_difficulty(
                properties, thickness
            ),
            "surface_finish_quality": self._calculate_surface_quality(
                properties, thickness
            ),
        }

    def _extract_processing_features(
        self, material_data: Dict, order_data: Dict
    ) -> Dict:
        """Признаки обработки материала."""
        material_type = material_data.get(
            "type", order_data.get("material_code", "MDF")
        )
        thickness = material_data.get(
            "thickness", order_data.get("thickness", 16.0)
        )

        properties = self.material_properties.get(
            material_type.upper(), self.material_properties["MDF"]
        )

        # Параметры резки
        feed_rate = self.cutting_parameters["feed_rate"]
        spindle_speed = self.cutting_parameters["spindle_speed"]
        tool_diameter = self.cutting_parameters["tool_diameter"]

        # Корректировка на основе материала
        adjusted_feed_rate = feed_rate * properties["cutting_speed"]
        adjusted_spindle_speed = spindle_speed * properties["cutting_speed"]

        # Расчет времени обработки
        sheet_size = self._get_sheet_size(material_type, material_data)
        processing_time = self._estimate_processing_time(
            sheet_size, thickness, properties
        )

        # Качество обработки
        edge_quality = self._estimate_edge_quality(properties, thickness)
        dimensional_accuracy = self._estimate_dimensional_accuracy(
            properties, thickness
        )

        return {
            "feed_rate_mm_min": adjusted_feed_rate,
            "spindle_speed_rpm": adjusted_spindle_speed,
            "tool_diameter_mm": tool_diameter,
            "estimated_processing_time_min": processing_time,
            "edge_quality": edge_quality,
            "dimensional_accuracy": dimensional_accuracy,
            "cutting_force_factor": self._calculate_cutting_force_factor(
                properties, thickness
            ),
            "tool_wear_factor": self._calculate_tool_wear_factor(
                properties, thickness
            ),
            "dust_generation_factor": self._calculate_dust_generation_factor(
                properties
            ),
            "noise_level_factor": self._calculate_noise_level_factor(
                properties, thickness
            ),
            "requires_special_tooling": self._requires_special_tooling(
                material_type, thickness
            ),
            "post_processing_required": self._requires_post_processing(
                material_type, thickness
            ),
        }

    def _get_sheet_size(
        self, material_type: str, material_data: Dict
    ) -> Tuple[float, float]:
        """Получить размеры листа материала."""
        # Приоритет: данные материала > стандартные размеры
        if "width" in material_data and "height" in material_data:
            return (material_data["width"], material_data["height"])

        # Стандартные размеры для типа материала
        properties = self.material_properties.get(
            material_type.upper(), self.material_properties["MDF"]
        )
        standard_sizes = properties["standard_sizes"]

        # Возвращаем первый стандартный размер
        return standard_sizes[0]

    def _is_standard_thickness(
        self, thickness: float, material_type: str
    ) -> bool:
        """Проверка стандартной толщины."""
        properties = self.material_properties.get(
            material_type.upper(), self.material_properties["MDF"]
        )
        thickness_range = properties["thickness_range"]

        # Стандартные толщины для МДФ
        standard_thicknesses = [3, 6, 8, 10, 12, 16, 18, 22, 25, 30, 40]

        return (
            thickness in standard_thicknesses
            and thickness_range[0] <= thickness <= thickness_range[1]
        )

    def _is_standard_size(
        self, sheet_size: Tuple[float, float], material_type: str
    ) -> bool:
        """Проверка стандартного размера."""
        properties = self.material_properties.get(
            material_type.upper(), self.material_properties["MDF"]
        )
        standard_sizes = properties["standard_sizes"]

        width, height = sheet_size
        for std_width, std_height in standard_sizes:
            if abs(width - std_width) < 10 and abs(height - std_height) < 10:
                return True

        return False

    def _calculate_material_strength(
        self, properties: Dict, thickness: float
    ) -> float:
        """Расчет прочности материала."""
        # Упрощенная модель прочности
        base_strength = properties["density"] / 750.0  # относительно МДФ
        thickness_factor = thickness / 16.0  # относительно стандартной толщины

        return base_strength * thickness_factor

    def _calculate_cutting_difficulty(
        self, properties: Dict, thickness: float
    ) -> float:
        """Расчет сложности резки."""
        # Факторы сложности
        hardness_factor = properties["hardness"]
        thickness_factor = thickness / 16.0
        density_factor = properties["density"] / 750.0

        # Сложность = среднее взвешенное факторов
        difficulty = (
            0.4 * hardness_factor
            + 0.3 * thickness_factor
            + 0.3 * density_factor
        )

        return min(difficulty, 1.0)

    def _calculate_surface_quality(
        self, properties: Dict, thickness: float
    ) -> float:
        """Расчет качества поверхности."""
        base_quality = properties["surface_quality"]
        thickness_factor = min(
            thickness / 16.0, 1.5
        )  # Толщина влияет на качество

        return min(base_quality * thickness_factor, 1.0)

    def _estimate_processing_time(
        self,
        sheet_size: Tuple[float, float],
        thickness: float,
        properties: Dict,
    ) -> float:
        """Оценка времени обработки."""
        width, height = sheet_size
        area = width * height

        # Базовое время на площадь (мин/м²)
        base_time_per_sqm = 2.0

        # Корректировки
        thickness_factor = thickness / 16.0
        material_factor = 1.0 / properties["cutting_speed"]

        processing_time = (
            (area / 1000000)
            * base_time_per_sqm
            * thickness_factor
            * material_factor
        )

        return processing_time

    def _estimate_edge_quality(
        self, properties: Dict, thickness: float
    ) -> float:
        """Оценка качества кромки."""
        base_quality = properties["surface_quality"]
        hardness_factor = properties["hardness"]

        # Твердость влияет на качество кромки
        edge_quality = base_quality * (0.7 + 0.3 * hardness_factor)

        return min(edge_quality, 1.0)

    def _estimate_dimensional_accuracy(
        self, properties: Dict, thickness: float
    ) -> float:
        """Оценка точности размеров."""
        # Плотность и твердость влияют на точность
        density_factor = properties["density"] / 750.0
        hardness_factor = properties["hardness"]

        accuracy = 0.8 * density_factor + 0.2 * hardness_factor

        return min(accuracy, 1.0)

    def _calculate_cutting_force_factor(
        self, properties: Dict, thickness: float
    ) -> float:
        """Расчет фактора силы резания."""
        density_factor = properties["density"] / 750.0
        hardness_factor = properties["hardness"]
        thickness_factor = thickness / 16.0

        force_factor = (
            0.4 * density_factor
            + 0.4 * hardness_factor
            + 0.2 * thickness_factor
        )

        return min(force_factor, 1.5)

    def _calculate_tool_wear_factor(
        self, properties: Dict, thickness: float
    ) -> float:
        """Расчет фактора износа инструмента."""
        hardness_factor = properties["hardness"]
        density_factor = properties["density"] / 750.0

        wear_factor = 0.6 * hardness_factor + 0.4 * density_factor

        return min(wear_factor, 1.2)

    def _calculate_dust_generation_factor(self, properties: Dict) -> float:
        """Расчет фактора образования пыли."""
        # Плотность влияет на образование пыли
        density_factor = properties["density"] / 750.0

        # Менее плотные материалы дают больше пыли
        dust_factor = 1.0 - 0.3 * density_factor

        return max(dust_factor, 0.3)

    def _calculate_noise_level_factor(
        self, properties: Dict, thickness: float
    ) -> float:
        """Расчет фактора уровня шума."""
        hardness_factor = properties["hardness"]
        thickness_factor = thickness / 16.0

        noise_factor = 0.5 * hardness_factor + 0.5 * thickness_factor

        return min(noise_factor, 1.2)

    def _requires_special_tooling(
        self, material_type: str, thickness: float
    ) -> bool:
        """Требуется ли специальный инструмент."""
        # Специальный инструмент для твердых материалов или большой толщины
        properties = self.material_properties.get(
            material_type.upper(), self.material_properties["MDF"]
        )

        return (
            properties["hardness"] > 0.8
            or thickness > 25
            or material_type.upper() in ["HDF", "массив"]
        )

    def _requires_post_processing(
        self, material_type: str, thickness: float
    ) -> bool:
        """Требуется ли постобработка."""
        # Постобработка для материалов с низким качеством поверхности
        properties = self.material_properties.get(
            material_type.upper(), self.material_properties["MDF"]
        )

        return properties[
            "surface_quality"
        ] < 0.7 or material_type.upper() in ["ДСП", "массив"]

    def _get_default_material_features(self) -> Dict:
        """Дефолтные признаки материалов."""
        return {
            # Базовые признаки
            "material_type": "MDF",
            "material_thickness": 16.0,
            "material_density": 750,
            "material_hardness": 0.7,
            "material_cost_factor": 1.0,
            "sheet_width": 2440,
            "sheet_height": 1220,
            "sheet_area": 2440 * 1220,
            "order_quantity": 1,
            "total_material_area": 2440 * 1220,
            "is_standard_thickness": True,
            "is_standard_size": True,
            # Технические признаки
            "sheet_volume_m3": 0.0476,
            "sheet_weight_kg": 35.7,
            "cutting_speed_factor": 1.0,
            "surface_quality": 0.8,
            "moisture_resistance": 0.6,
            "thickness_factor": 1.0,
            "density_factor": 1.0,
            "hardness_factor": 0.7,
            "material_strength": 1.0,
            "cutting_difficulty": 0.7,
            "surface_finish_quality": 0.8,
            # Признаки обработки
            "feed_rate_mm_min": 5000,
            "spindle_speed_rpm": 18000,
            "tool_diameter_mm": 6.35,
            "estimated_processing_time_min": 2.0,
            "edge_quality": 0.8,
            "dimensional_accuracy": 0.8,
            "cutting_force_factor": 1.0,
            "tool_wear_factor": 1.0,
            "dust_generation_factor": 0.7,
            "noise_level_factor": 1.0,
            "requires_special_tooling": False,
            "post_processing_required": False,
        }
