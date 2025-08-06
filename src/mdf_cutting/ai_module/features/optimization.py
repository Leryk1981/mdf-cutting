"""
Извлечение признаков оптимизации раскроя.

Этот модуль содержит:
- Признаки материалов
- Признаки процесса резки
- Признаки эффективности оптимизации
"""

import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class OptimizationFeatureExtractor:
    """Извлечение признаков, связанных с оптимизацией раскроя"""
    
    def __init__(self):
        """Инициализация экстрактора признаков оптимизации."""
        # Справочник плотностей материалов (кг/м³)
        self.material_densities = {
            "MDF": 750,
            "MDF16": 750,
            "MDF18": 750,
            "MDF22": 750,
            "HDF": 850,
            "ДСП": 650,
            "фанера": 600,
            "массив": 500
        }
        
        # Технологические параметры
        self.kerf_width = 3.2  # мм - ширина реза
        self.min_cut_length = 5  # мм - минимальная длина реза
        self.safety_margin = 2.0  # мм - безопасный отступ
    
    def extract_features(self, dxf_data: Dict, order_data: Dict) -> Dict[str, Any]:
        """
        Извлечь признаки оптимизации.
        
        Args:
            dxf_data: Данные из DXF файла
            order_data: Данные заказа
            
        Returns:
            Dict: Словарь с признаками оптимизации
        """
        try:
            material_features = self._extract_material_features(dxf_data, order_data)
            cutting_features = self._extract_cutting_features(dxf_data)
            efficiency_features = self._extract_efficiency_features(dxf_data)
            
            return {
                **material_features,
                **cutting_features,
                **efficiency_features
            }
        except Exception as e:
            logger.error(f"Ошибка извлечения признаков оптимизации: {e}")
            return self._get_default_optimization_features()
    
    def _extract_material_features(self, dxf_data: Dict, order_data: Dict) -> Dict:
        """Признаки, связанные с материалом."""
        # Получаем информацию о материале из заказа
        material_thickness = order_data.get("thickness", 16.0)
        material_type = order_data.get("material_code", "MDF")
        material_quantity = order_data.get("quantity", 1)
        
        # Рассчитываем суммарную площадь использованного материала
        pieces_area = self._calculate_total_pieces_area(dxf_data)
        
        # Плотность материала
        material_density = self._get_material_density(material_type)
        
        # Масса материала
        material_volume = pieces_area * material_thickness / 1000000  # м³
        material_weight = material_volume * material_density
        
        return {
            "material_thickness": material_thickness,
            "material_type_code": material_type,
            "is_mdf": 1 if "MDF" in material_type.upper() else 0,
            "is_hdf": 1 if "HDF" in material_type.upper() else 0,
            "is_dsp": 1 if "ДСП" in material_type.upper() else 0,
            "material_used_area": pieces_area,
            "material_density": material_density,
            "material_weight_kg": material_weight,
            "material_volume_m3": material_volume,
            "order_quantity": material_quantity,
            "material_cost_factor": self._calculate_material_cost_factor(material_type, material_thickness)
        }
    
    def _extract_cutting_features(self, dxf_data: Dict) -> Dict:
        """Признаки, связанные с процессом резки."""
        # Подсчет линий реза
        cut_lines = [e for e in dxf_data.get("entities", []) 
                    if e["type"] in ["LINE", "LWPOLYLINE"]]
        
        # Оценка общей длины реза
        total_cut_length = sum(self._get_entity_length(e) for e in cut_lines)
        
        # Количество сложных резов (не прямых)
        complex_cuts = len([e for e in cut_lines if self._is_complex_cut(e)])
        
        # Время резки (примерная оценка)
        cutting_time = self._estimate_cutting_time(total_cut_length, complex_cuts)
        
        # Эффективность резки
        cutting_efficiency = self._calculate_cutting_efficiency(cut_lines, dxf_data)
        
        return {
            "total_cut_length": total_cut_length,
            "num_cut_operations": len(cut_lines),
            "complex_cut_ratio": complex_cuts / len(cut_lines) if cut_lines else 0,
            "avg_cut_length": total_cut_length / len(cut_lines) if cut_lines else 0,
            "estimated_cutting_time_min": cutting_time,
            "cutting_efficiency": cutting_efficiency,
            "kerf_waste_area": total_cut_length * self.kerf_width,
            "straight_cuts_count": len(cut_lines) - complex_cuts,
            "curved_cuts_count": complex_cuts
        }
    
    def _extract_efficiency_features(self, dxf_data: Dict) -> Dict:
        """Признаки эффективности текущей оптимизации."""
        pieces = self._get_pieces_info(dxf_data)
        
        if not pieces:
            return self._get_default_efficiency_features()
        
        # Статистики по размерам деталей
        areas = [p["area"] for p in pieces]
        perimeters = [p["perimeter"] for p in pieces]
        
        # Эффективность использования материала
        total_area = sum(areas)
        sheet_area = self._estimate_sheet_area(dxf_data)
        utilization_rate = (total_area / sheet_area) * 100 if sheet_area > 0 else 0
        
        # Геометрическая эффективность
        geometric_efficiency = self._calculate_geometric_efficiency(dxf_data)
        
        # Оценка отходов
        waste_analysis = self._analyze_waste_patterns(dxf_data)
        
        return {
            "piece_size_variance": np.var(areas) if len(areas) > 1 else 0,
            "piece_size_range": max(areas) - min(areas) if areas else 0,
            "large_pieces_ratio": len([a for a in areas if a > np.median(areas)]) / len(areas) if areas else 0,
            "small_pieces_ratio": len([a for a in areas if a < np.percentile(areas, 25)]) / len(areas) if areas else 0,
            "geometric_efficiency": geometric_efficiency,
            "utilization_rate": utilization_rate,
            "waste_percentage": 100 - utilization_rate,
            "avg_piece_area": np.mean(areas) if areas else 0,
            "avg_piece_perimeter": np.mean(perimeters) if perimeters else 0,
            "piece_count": len(pieces),
            "waste_pattern_score": waste_analysis["pattern_score"],
            "waste_clustering": waste_analysis["clustering_score"],
            "optimization_potential": self._estimate_optimization_potential(dxf_data)
        }
    
    def _calculate_total_pieces_area(self, dxf_data: Dict) -> float:
        """Вычисление общей площади деталей."""
        total_area = 0
        
        for entity in dxf_data.get("entities", []):
            if entity["type"] in ["LWPOLYLINE", "POLYLINE"]:
                area = self._calculate_polygon_area(entity.get("points", []))
                total_area += area
            elif entity["type"] == "CIRCLE":
                radius = entity.get("radius", 0)
                area = np.pi * radius ** 2
                total_area += area
        
        return total_area
    
    def _calculate_polygon_area(self, points: List[List[float]]) -> float:
        """Вычисление площади многоугольника по формуле Гаусса."""
        if len(points) < 3:
            return 0
        
        area = 0
        for i in range(len(points)):
            j = (i + 1) % len(points)
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        
        return abs(area) / 2
    
    def _get_material_density(self, material_type: str) -> float:
        """Получение плотности материала."""
        material_upper = material_type.upper()
        
        for key, density in self.material_densities.items():
            if key.upper() in material_upper:
                return density
        
        return self.material_densities["MDF"]  # Дефолтное значение
    
    def _calculate_material_cost_factor(self, material_type: str, thickness: float) -> float:
        """Расчет фактора стоимости материала."""
        base_cost = 1.0
        
        # Корректировка по типу материала
        if "HDF" in material_type.upper():
            base_cost *= 1.2
        elif "ДСП" in material_type.upper():
            base_cost *= 0.8
        elif "фанера" in material_type.upper():
            base_cost *= 1.5
        
        # Корректировка по толщине
        thickness_factor = thickness / 16.0  # относительно стандартной толщины 16мм
        base_cost *= thickness_factor
        
        return base_cost
    
    def _get_entity_length(self, entity: Dict) -> float:
        """Вычисление длины сущности."""
        if entity["type"] == "LINE":
            start = entity.get("start", [0, 0])
            end = entity.get("end", [0, 0])
            return np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        elif entity["type"] == "LWPOLYLINE":
            points = entity.get("points", [])
            if len(points) < 2:
                return 0
            
            total_length = 0
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]
                length = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                total_length += length
            
            return total_length
        
        return 0
    
    def _is_complex_cut(self, entity: Dict) -> bool:
        """Определение сложности реза."""
        if entity["type"] == "LINE":
            return False  # Прямой рез
        
        elif entity["type"] == "LWPOLYLINE":
            points = entity.get("points", [])
            if len(points) <= 2:
                return False
            
            # Проверяем, насколько прямая линия
            if len(points) == 3:
                # Трехточечная линия - проверяем прямолинейность
                p1, p2, p3 = points
                v1 = [p2[0] - p1[0], p2[1] - p1[1]]
                v2 = [p3[0] - p2[0], p3[1] - p2[1]]
                
                # Нормализуем векторы
                len1 = np.sqrt(v1[0]**2 + v1[1]**2)
                len2 = np.sqrt(v2[0]**2 + v2[1]**2)
                
                if len1 > 0 and len2 > 0:
                    v1_norm = [v1[0]/len1, v1[1]/len1]
                    v2_norm = [v2[0]/len2, v2[1]/len2]
                    
                    # Скалярное произведение
                    dot_product = v1_norm[0]*v2_norm[0] + v1_norm[1]*v2_norm[1]
                    angle = np.arccos(np.clip(dot_product, -1, 1))
                    
                    return angle > 0.1  # Если угол больше ~6 градусов
            
            return len(points) > 3  # Многоточечная линия
        
        return True
    
    def _estimate_cutting_time(self, total_length: float, complex_cuts: int) -> float:
        """Оценка времени резки."""
        # Базовые скорости (мм/мин)
        straight_speed = 5000  # Прямой рез
        complex_speed = 2000   # Сложный рез
        
        # Разделяем на прямые и сложные резы
        straight_length = total_length * 0.7  # Примерно 70% прямых резов
        complex_length = total_length * 0.3   # Примерно 30% сложных резов
        
        # Время резки
        straight_time = straight_length / straight_speed
        complex_time = complex_length / complex_speed
        
        # Дополнительное время на сложные резы
        setup_time = complex_cuts * 0.5  # 30 секунд на сложный рез
        
        return straight_time + complex_time + setup_time
    
    def _calculate_cutting_efficiency(self, cut_lines: List[Dict], dxf_data: Dict) -> float:
        """Расчет эффективности резки."""
        if not cut_lines:
            return 0.0
        
        total_length = sum(self._get_entity_length(line) for line in cut_lines)
        pieces_area = self._calculate_total_pieces_area(dxf_data)
        
        if pieces_area == 0:
            return 0.0
        
        # Эффективность = площадь деталей / длина реза
        # Чем больше площадь при меньшей длине реза, тем эффективнее
        efficiency = pieces_area / total_length if total_length > 0 else 0
        
        # Нормализуем к диапазону 0-1
        return min(efficiency / 1000, 1.0)  # Эмпирическая нормализация
    
    def _get_pieces_info(self, dxf_data: Dict) -> List[Dict]:
        """Получение информации о деталях."""
        pieces = []
        
        for entity in dxf_data.get("entities", []):
            if entity["type"] in ["LWPOLYLINE", "POLYLINE"]:
                points = entity.get("points", [])
                if len(points) >= 3:
                    area = self._calculate_polygon_area(points)
                    perimeter = self._calculate_polygon_perimeter(points)
                    
                    pieces.append({
                        "area": area,
                        "perimeter": perimeter,
                        "type": entity["type"]
                    })
            
            elif entity["type"] == "CIRCLE":
                radius = entity.get("radius", 0)
                area = np.pi * radius ** 2
                perimeter = 2 * np.pi * radius
                
                pieces.append({
                    "area": area,
                    "perimeter": perimeter,
                    "type": entity["type"]
                })
        
        return pieces
    
    def _calculate_polygon_perimeter(self, points: List[List[float]]) -> float:
        """Вычисление периметра многоугольника."""
        if len(points) < 2:
            return 0
        
        perimeter = 0
        for i in range(len(points)):
            j = (i + 1) % len(points)
            p1, p2 = points[i], points[j]
            length = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            perimeter += length
        
        return perimeter
    
    def _estimate_sheet_area(self, dxf_data: Dict) -> float:
        """Оценка площади листа материала."""
        # Получаем границы всех сущностей
        all_x = []
        all_y = []
        
        for entity in dxf_data.get("entities", []):
            if entity["type"] in ["LWPOLYLINE", "POLYLINE"]:
                points = entity.get("points", [])
                for point in points:
                    all_x.append(point[0])
                    all_y.append(point[1])
            
            elif entity["type"] == "CIRCLE":
                center = entity.get("center", [0, 0])
                radius = entity.get("radius", 0)
                all_x.extend([center[0] - radius, center[0] + radius])
                all_y.extend([center[1] - radius, center[1] + radius])
        
        if not all_x or not all_y:
            return 2440 * 1220  # Стандартный лист МДФ
        
        # Добавляем отступы
        margin = 50  # мм
        width = max(all_x) - min(all_x) + 2 * margin
        height = max(all_y) - min(all_y) + 2 * margin
        
        return width * height
    
    def _calculate_geometric_efficiency(self, dxf_data: Dict) -> float:
        """Расчет геометрической эффективности."""
        pieces = self._get_pieces_info(dxf_data)
        if not pieces:
            return 0.0
        
        # Эффективность на основе формы деталей
        efficiencies = []
        for piece in pieces:
            area = piece["area"]
            perimeter = piece["perimeter"]
            
            if perimeter > 0:
                # Коэффициент компактности (круг имеет максимум = 1)
                compactness = (4 * np.pi * area) / (perimeter ** 2)
                efficiencies.append(compactness)
        
        return np.mean(efficiencies) if efficiencies else 0.0
    
    def _analyze_waste_patterns(self, dxf_data: Dict) -> Dict:
        """Анализ паттернов отходов."""
        # Упрощенный анализ - в реальности нужен более сложный алгоритм
        pieces = self._get_pieces_info(dxf_data)
        total_area = sum(p["area"] for p in pieces)
        sheet_area = self._estimate_sheet_area(dxf_data)
        
        waste_area = sheet_area - total_area
        waste_percentage = (waste_area / sheet_area) * 100 if sheet_area > 0 else 0
        
        # Оценка паттерна отходов
        if waste_percentage < 10:
            pattern_score = 0.9  # Отличная оптимизация
        elif waste_percentage < 20:
            pattern_score = 0.7  # Хорошая оптимизация
        elif waste_percentage < 30:
            pattern_score = 0.5  # Средняя оптимизация
        else:
            pattern_score = 0.3  # Плохая оптимизация
        
        # Оценка кластеризации отходов
        clustering_score = self._estimate_waste_clustering(dxf_data)
        
        return {
            "pattern_score": pattern_score,
            "clustering_score": clustering_score,
            "waste_percentage": waste_percentage
        }
    
    def _estimate_waste_clustering(self, dxf_data: Dict) -> float:
        """Оценка кластеризации отходов."""
        # Упрощенная реализация
        # В реальности нужно анализировать пространственное распределение
        pieces = self._get_pieces_info(dxf_data)
        
        if len(pieces) < 2:
            return 0.5
        
        # Оценка на основе размера деталей
        areas = [p["area"] for p in pieces]
        area_variance = np.var(areas)
        
        # Меньшая дисперсия = лучшее использование материала
        clustering_score = 1.0 / (1.0 + area_variance / 10000)
        
        return min(clustering_score, 1.0)
    
    def _estimate_optimization_potential(self, dxf_data: Dict) -> float:
        """Оценка потенциала оптимизации."""
        pieces = self._get_pieces_info(dxf_data)
        if not pieces:
            return 0.0
        
        # Факторы для оценки потенциала
        areas = [p["area"] for p in pieces]
        total_area = sum(areas)
        sheet_area = self._estimate_sheet_area(dxf_data)
        
        utilization_rate = (total_area / sheet_area) * 100 if sheet_area > 0 else 0
        
        # Потенциал обратно пропорционален текущей эффективности
        potential = max(0, (100 - utilization_rate) / 100)
        
        # Корректировка на основе количества деталей
        piece_count_factor = min(len(pieces) / 20, 1.0)  # Больше деталей = больше потенциал
        
        # Корректировка на основе размера деталей
        avg_area = np.mean(areas)
        size_factor = min(avg_area / 10000, 1.0)  # Меньшие детали = больше потенциал
        
        return potential * (0.5 + 0.3 * piece_count_factor + 0.2 * size_factor)
    
    def _get_default_optimization_features(self) -> Dict:
        """Дефолтные признаки оптимизации."""
        return {
            # Материальные признаки
            "material_thickness": 16.0,
            "material_type_code": "MDF",
            "is_mdf": 1,
            "is_hdf": 0,
            "is_dsp": 0,
            "material_used_area": 0,
            "material_density": 750,
            "material_weight_kg": 0,
            "material_volume_m3": 0,
            "order_quantity": 1,
            "material_cost_factor": 1.0,
            
            # Признаки резки
            "total_cut_length": 0,
            "num_cut_operations": 0,
            "complex_cut_ratio": 0,
            "avg_cut_length": 0,
            "estimated_cutting_time_min": 0,
            "cutting_efficiency": 0,
            "kerf_waste_area": 0,
            "straight_cuts_count": 0,
            "curved_cuts_count": 0,
            
            # Признаки эффективности
            "piece_size_variance": 0,
            "piece_size_range": 0,
            "large_pieces_ratio": 0,
            "small_pieces_ratio": 0,
            "geometric_efficiency": 0,
            "utilization_rate": 0,
            "waste_percentage": 100,
            "avg_piece_area": 0,
            "avg_piece_perimeter": 0,
            "piece_count": 0,
            "waste_pattern_score": 0,
            "waste_clustering": 0,
            "optimization_potential": 1.0
        }
    
    def _get_default_efficiency_features(self) -> Dict:
        """Дефолтные признаки эффективности."""
        return {
            "piece_size_variance": 0,
            "piece_size_range": 0,
            "large_pieces_ratio": 0,
            "small_pieces_ratio": 0,
            "geometric_efficiency": 0,
            "utilization_rate": 0,
            "waste_percentage": 100,
            "avg_piece_area": 0,
            "avg_piece_perimeter": 0,
            "piece_count": 0,
            "waste_pattern_score": 0,
            "waste_clustering": 0,
            "optimization_potential": 1.0
        } 