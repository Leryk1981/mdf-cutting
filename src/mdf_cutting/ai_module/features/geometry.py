"""
Извлечение геометрических признаков из DXF данных.

Этот модуль содержит:
- Парсинг полигонов деталей
- Извлечение глобальных и локальных признаков
- Пространственные и топологические характеристики
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging
from pathlib import Path

try:
    from shapely.geometry import Polygon, MultiPolygon, Point
    from shapely.ops import unary_union
    import networkx as nx
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    logging.warning("Shapely не установлен. Геометрические признаки будут ограничены.")

logger = logging.getLogger(__name__)


class GeometryFeatureExtractor:
    """Извлечение геометрических признаков из DXF данных"""
    
    def __init__(self):
        """Инициализация экстрактора признаков."""
        self.pieces_cache = {}
        
        if not SHAPELY_AVAILABLE:
            logger.warning("Shapely недоступен. Используется упрощенный режим.")
    
    def extract_features(self, dxf_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлечь все геометрические признаки.
        
        Args:
            dxf_data: Данные из DXF файла
            
        Returns:
            Dict: Словарь с геометрическими признаками
        """
        try:
            if SHAPELY_AVAILABLE:
                pieces = self._parse_pieces_polygons(dxf_data)
                sheet_polygon = self._get_sheet_polygon(dxf_data)
                
                return {
                    "global_features": self._extract_global_features(pieces, sheet_polygon),
                    "local_features": self._extract_local_features(pieces, sheet_polygon),
                    "spatial_features": self._extract_spatial_features(pieces, sheet_polygon),
                    "topological_features": self._extract_topological_features(pieces)
                }
            else:
                # Упрощенный режим без Shapely
                return self._extract_simple_features(dxf_data)
                
        except Exception as e:
            logger.error(f"Ошибка извлечения геометрических признаков: {e}")
            return self._get_default_features()
    
    def _parse_pieces_polygons(self, dxf_data: Dict) -> List[Polygon]:
        """Преобразовать DXF сущности в Shapely полигоны."""
        polygons = []
        
        for entity in dxf_data.get("entities", []):
            try:
                if entity["type"] in ["LWPOLYLINE", "POLYLINE"]:
                    points = entity.get("points", [])
                    if len(points) >= 3:
                        # Преобразование точек в формат для Shapely
                        coords = [(p[0], p[1]) for p in points]
                        polygon = Polygon(coords)
                        if polygon.is_valid and polygon.area > 0:
                            polygons.append(polygon)
                            
                elif entity["type"] == "CIRCLE":
                    center = entity.get("center", [0, 0])
                    radius = entity.get("radius", 0)
                    if radius > 0:
                        circle = Point(center[0], center[1]).buffer(radius)
                        polygons.append(circle)
                        
            except Exception as e:
                logger.warning(f"Ошибка парсинга сущности {entity.get('type', 'unknown')}: {e}")
                continue
        
        return polygons
    
    def _get_sheet_polygon(self, dxf_data: Dict) -> Polygon:
        """Получить полигон листа материала."""
        # Получаем границы всех сущностей
        all_points = []
        
        for entity in dxf_data.get("entities", []):
            if entity["type"] in ["LWPOLYLINE", "POLYLINE"]:
                points = entity.get("points", [])
                all_points.extend([(p[0], p[1]) for p in points])
            elif entity["type"] == "CIRCLE":
                center = entity.get("center", [0, 0])
                radius = entity.get("radius", 0)
                all_points.extend([
                    (center[0] - radius, center[1] - radius),
                    (center[0] + radius, center[1] + radius)
                ])
        
        if not all_points:
            # Дефолтный лист 2440x1220 мм
            return Polygon([(0, 0), (2440, 0), (2440, 1220), (0, 1220)])
        
        # Создаем bounding box с отступом
        x_coords = [p[0] for p in all_points]
        y_coords = [p[1] for p in all_points]
        
        margin = 50  # мм отступ
        min_x, max_x = min(x_coords) - margin, max(x_coords) + margin
        min_y, max_y = min(y_coords) - margin, max(y_coords) + margin
        
        return Polygon([(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)])
    
    def _extract_global_features(self, pieces: List[Polygon], sheet: Polygon) -> Dict:
        """Глобальные признаки всей карты раскроя."""
        if not pieces:
            return self._get_default_global_features()
        
        try:
            pieces_area = sum(p.area for p in pieces)
            sheet_area = sheet.area
            
            # Конвалуция всех деталей
            union_pieces = unary_union(pieces)
            
            # Отходы (пустые области)
            waste_area = sheet_area - pieces_area
            
            return {
                "total_pieces": len(pieces),
                "total_area": pieces_area,
                "waste_area": waste_area,
                "waste_percentage": (waste_area / sheet_area) * 100 if sheet_area > 0 else 0,
                "utilization_rate": (pieces_area / sheet_area) * 100 if sheet_area > 0 else 0,
                "pieces_complexity": self._calculate_complexity(pieces),
                "sheet_coverage": self._calculate_coverage(union_pieces, sheet),
                "avg_piece_area": pieces_area / len(pieces) if pieces else 0,
                "piece_area_variance": np.var([p.area for p in pieces]) if len(pieces) > 1 else 0
            }
        except Exception as e:
            logger.error(f"Ошибка извлечения глобальных признаков: {e}")
            return self._get_default_global_features()
    
    def _extract_local_features(self, pieces: List[Polygon], sheet: Polygon) -> Dict:
        """Локальные признаки для каждой детали."""
        local_features = []
        
        try:
            for i, piece in enumerate(pieces):
                # Расстояние до края листа
                sheet_boundary = sheet.exterior
                piece_center = piece.centroid
                
                # Минимальное расстояние до границы листа
                min_dist_to_edge = piece_center.distance(sheet_boundary)
                
                # Расстояния до соседних деталей
                neighbor_distances = []
                for j, other in enumerate(pieces):
                    if i != j:
                        dist = piece.distance(other)
                        if dist > 0:
                            neighbor_distances.append(dist)
                
                # Аспекты геометрии
                min_rect = piece.minimum_rotated_rectangle
                width, height = self._get_rect_dimensions(min_rect)
                aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 1
                
                local_features.append({
                    "piece_id": i,
                    "area": piece.area,
                    "perimeter": piece.length,
                    "compactness": (4 * np.pi * piece.area) / (piece.length ** 2) if piece.length > 0 else 0,
                    "min_dist_to_edge": min_dist_to_edge,
                    "avg_neighbor_dist": np.mean(neighbor_distances) if neighbor_distances else 0,
                    "aspect_ratio": aspect_ratio,
                    "rectilinearity": self._calculate_rectilinearity(piece),
                    "is_near_edge": min_dist_to_edge < 50,  # Близко к краю
                    "neighbor_count": len([d for d in neighbor_distances if d < 20])  # Количество соседей
                })
        except Exception as e:
            logger.error(f"Ошибка извлечения локальных признаков: {e}")
        
        return {"pieces_features": local_features}
    
    def _extract_spatial_features(self, pieces: List[Polygon], sheet: Polygon) -> Dict:
        """Пространственные признаки расположения деталей."""
        if not pieces:
            return self._get_default_spatial_features()
        
        try:
            # Кластеризация деталей в разных зонах листа
            # Разделим лист на 4 квадранта
            minx, miny, maxx, maxy = sheet.bounds
            cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
            
            quadrants = {
                "Q1": 0,  # правый верхний
                "Q2": 0,  # левый верхний
                "Q3": 0,  # левый нижний
                "Q4": 0   # правый нижний
            }
            
            centroids = [piece.centroid for piece in pieces]
            for centroid in centroids:
                x, y = centroid.x, centroid.y
                if x >= cx and y >= cy:
                    quadrants["Q1"] += 1
                elif x < cx and y >= cy:
                    quadrants["Q2"] += 1
                elif x < cx and y < cy:
                    quadrants["Q3"] += 1
                else:
                    quadrants["Q4"] += 1
            
            # Равномерность распределения
            total_pieces = len(pieces)
            ideal_per_quadrant = total_pieces / 4
            distribution_evenness = 1 - (np.std(list(quadrants.values())) / ideal_per_quadrant) if ideal_per_quadrant > 0 else 0
            
            return {
                "quadrants_distribution": quadrants,
                "distribution_evenness": max(0, distribution_evenness),
                "spatial_dispersion": self._calculate_spatial_dispersion(centroids, sheet),
                "centroid_x_mean": np.mean([c.x for c in centroids]),
                "centroid_y_mean": np.mean([c.y for c in centroids]),
                "centroid_x_std": np.std([c.x for c in centroids]),
                "centroid_y_std": np.std([c.y for c in centroids])
            }
        except Exception as e:
            logger.error(f"Ошибка извлечения пространственных признаков: {e}")
            return self._get_default_spatial_features()
    
    def _extract_topological_features(self, pieces: List[Polygon]) -> Dict:
        """Топологические признаки (связность, соседство)."""
        if not SHAPELY_AVAILABLE or len(pieces) < 2:
            return self._get_default_topological_features()
        
        try:
            # Создаем граф соседства деталей
            G = nx.Graph()
            
            for i, piece in enumerate(pieces):
                G.add_node(i, piece=piece)
            
            # Добавляем ребра между соседними деталями
            for i in range(len(pieces)):
                for j in range(i + 1, len(pieces)):
                    if pieces[i].distance(pieces[j]) < 1.0:  # Порог соседства
                        G.add_edge(i, j)
            
            # Вычисляем характеристики графа
            graph_features = {}
            if G.number_of_nodes() > 0:
                graph_features = {
                    "avg_degree": np.mean([d for n, d in G.degree()]),
                    "num_connected_components": nx.number_connected_components(G),
                    "avg_clustering": nx.average_clustering(G) if G.number_of_edges() > 0 else 0,
                    "graph_density": nx.density(G),
                    "max_degree": max([d for n, d in G.degree()]) if G.number_of_nodes() > 0 else 0,
                    "isolated_nodes": len(list(nx.isolates(G)))
                }
            
            return {"topological_features": graph_features}
        except Exception as e:
            logger.error(f"Ошибка извлечения топологических признаков: {e}")
            return self._get_default_topological_features()
    
    def _extract_simple_features(self, dxf_data: Dict) -> Dict:
        """Упрощенное извлечение признаков без Shapely."""
        entities = dxf_data.get("entities", [])
        
        # Подсчет сущностей
        polyline_count = len([e for e in entities if e["type"] in ["LWPOLYLINE", "POLYLINE"]])
        circle_count = len([e for e in entities if e["type"] == "CIRCLE"])
        
        # Простая оценка площади
        total_area = 0
        for entity in entities:
            if entity["type"] in ["LWPOLYLINE", "POLYLINE"]:
                points = entity.get("points", [])
                if len(points) >= 3:
                    # Простая формула площади многоугольника
                    area = self._calculate_polygon_area(points)
                    total_area += area
            elif entity["type"] == "CIRCLE":
                radius = entity.get("radius", 0)
                area = np.pi * radius ** 2
                total_area += area
        
        return {
            "global_features": {
                "total_pieces": polyline_count + circle_count,
                "total_area": total_area,
                "waste_percentage": 0,  # Не можем вычислить без Shapely
                "utilization_rate": 0,
                "pieces_complexity": 0
            },
            "local_features": {"pieces_features": []},
            "spatial_features": {"quadrants_distribution": {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}},
            "topological_features": {"topological_features": {}}
        }
    
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
    
    def _get_rect_dimensions(self, rect: Polygon) -> Tuple[float, float]:
        """Получить размеры прямоугольника."""
        coords = list(rect.exterior.coords)
        if len(coords) < 4:
            return 0, 0
        
        # Вычисляем длины сторон
        side1 = np.sqrt((coords[1][0] - coords[0][0])**2 + (coords[1][1] - coords[0][1])**2)
        side2 = np.sqrt((coords[2][0] - coords[1][0])**2 + (coords[2][1] - coords[1][1])**2)
        
        return min(side1, side2), max(side1, side2)
    
    def _calculate_rectilinearity(self, polygon: Polygon) -> float:
        """Вычисление прямолинейности полигона."""
        try:
            # Сравниваем с минимальным ограничивающим прямоугольником
            min_rect = polygon.minimum_rotated_rectangle
            rect_area = min_rect.area
            poly_area = polygon.area
            
            return poly_area / rect_area if rect_area > 0 else 0
        except:
            return 0
    
    def _calculate_complexity(self, pieces: List[Polygon]) -> float:
        """Оценка сложности расположения деталей."""
        if len(pieces) < 2:
            return 0.0
        
        try:
            total_interactions = 0
            for i in range(len(pieces)):
                for j in range(i + 1, len(pieces)):
                    if pieces[i].intersects(pieces[j]):
                        total_interactions += 1
            
            return total_interactions / len(pieces)
        except:
            return 0.0
    
    def _calculate_coverage(self, union_pieces: Polygon, sheet: Polygon) -> float:
        """Оценка покрытия листа деталями."""
        try:
            if sheet.area == 0:
                return 0.0
            
            intersection = sheet.intersection(union_pieces)
            return intersection.area / sheet.area
        except:
            return 0.0
    
    def _calculate_spatial_dispersion(self, centroids: List[Point], sheet: Polygon) -> float:
        """Вычисление пространственной дисперсии."""
        if len(centroids) < 2:
            return 0.0
        
        try:
            # Вычисляем среднее расстояние между центрами
            distances = []
            for i in range(len(centroids)):
                for j in range(i + 1, len(centroids)):
                    dist = centroids[i].distance(centroids[j])
                    distances.append(dist)
            
            return np.std(distances) if distances else 0.0
        except:
            return 0.0
    
    def _get_default_features(self) -> Dict:
        """Возвращает дефолтные признаки при ошибке."""
        return {
            "global_features": self._get_default_global_features(),
            "local_features": {"pieces_features": []},
            "spatial_features": self._get_default_spatial_features(),
            "topological_features": self._get_default_topological_features()
        }
    
    def _get_default_global_features(self) -> Dict:
        """Дефолтные глобальные признаки."""
        return {
            "total_pieces": 0,
            "total_area": 0,
            "waste_area": 0,
            "waste_percentage": 0,
            "utilization_rate": 0,
            "pieces_complexity": 0,
            "sheet_coverage": 0,
            "avg_piece_area": 0,
            "piece_area_variance": 0
        }
    
    def _get_default_spatial_features(self) -> Dict:
        """Дефолтные пространственные признаки."""
        return {
            "quadrants_distribution": {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0},
            "distribution_evenness": 0,
            "spatial_dispersion": 0,
            "centroid_x_mean": 0,
            "centroid_y_mean": 0,
            "centroid_x_std": 0,
            "centroid_y_std": 0
        }
    
    def _get_default_topological_features(self) -> Dict:
        """Дефолтные топологические признаки."""
        return {
            "topological_features": {
                "avg_degree": 0,
                "num_connected_components": 0,
                "avg_clustering": 0,
                "graph_density": 0,
                "max_degree": 0,
                "isolated_nodes": 0
            }
        } 