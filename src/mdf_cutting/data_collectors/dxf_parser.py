"""
Парсер DXF файлов для извлечения данных карт раскроя.

Этот модуль содержит:
- Парсинг DXF файлов с помощью ezdxf
- Извлечение геометрических данных
- Определение областей отходов
- Валидацию геометрических данных
- Статистику использования материала
"""

import ezdxf
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from ..config.loader import ConfigLoader
from .schemas import DxfData, DxfEntity, DxfMetadata, DxfStatistics


def calculate_area(points: List[List[float]]) -> float:
    """
    Вычисляет площадь многоугольника по точкам.

    Args:
        points: Список точек [(x, y), ...]

    Returns:
        float: Площадь многоугольника
    """
    if len(points) < 3:
        return 0.0

    # Формула площади многоугольника (формула шнурка)
    area = 0.0
    for i in range(len(points)):
        j = (i + 1) % len(points)
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]

    return abs(area) / 2.0


class DxfParser:
    """
    Парсер DXF файлов для извлечения данных карт раскроя.

    Обеспечивает полный парсинг DXF файлов с извлечением геометрии,
    определением областей отходов и статистикой использования материала.
    """

    def __init__(self, config_loader: ConfigLoader):
        """
        Инициализация парсера DXF.

        Args:
            config_loader: Загрузчик конфигурации
        """
        self.config = config_loader
        self.config.load_all()
        self.min_utilizable_area = self._get_minimum_utilizable_area()

    def parse_cutting_map(self, dxf_path: Path) -> DxfData:
        """
        Распарсить DXF файл с картой раскроя.

        Args:
            dxf_path: Путь к DXF файлу

        Returns:
            DxfData: Структурированные данные из DXF

        Raises:
            ValueError: При ошибках чтения или парсинга DXF
        """
        try:
            doc = ezdxf.readfile(str(dxf_path))
        except IOError as e:
            raise ValueError(f"Не удалось прочитать DXF файл: {e}")
        except ezdxf.DXFStructureError as e:
            raise ValueError(f"Некорректная структура DXF: {e}")

        msp = doc.modelspace()

        # Извлекаем все компоненты
        metadata = self._extract_metadata(doc, dxf_path)
        entities = self._parse_entities(msp)
        dimensions = self._get_dimensions(msp)
        material_info = self._extract_material_info(doc)
        statistics = self._calculate_statistics(entities, dimensions)

        return DxfData(
            metadata=metadata,
            entities=entities,
            statistics=statistics,
            dimensions=dimensions,
            material_info=material_info,
        )

    def extract_raw_pieces(self, dxf_data: DxfData) -> List[Dict[str, Any]]:
        """
        Извлечь данные о заготовках из DXF.

        Args:
            dxf_data: Данные из DXF файла

        Returns:
            List[Dict]: Список заготовок с геометрией
        """
        pieces = []

        for entity in dxf_data.entities:
            if entity.type in ["LWPOLYLINE", "POLYLINE", "CIRCLE"]:
                piece = {
                    "id": entity.handle,
                    "geometry": entity.points or [],
                    "area": entity.area,
                    "bounding_box": entity.bounding_box or [],
                    "layer": entity.layer,
                    "color": entity.color,
                    "type": entity.type,
                }
                pieces.append(piece)

        return pieces

    def extract_waste_areas(self, dxf_data: DxfData) -> List[Dict[str, Any]]:
        """
        Определить области отходов между деталями.

        Args:
            dxf_data: Данные из DXF файла

        Returns:
            List[Dict]: Список областей отходов
        """
        pieces = self.extract_raw_pieces(dxf_data)
        waste_areas = []

        # Найти общую площадь листа
        total_area = dxf_data.statistics.total_area

        # Вычесть площадь деталей
        pieces_area = sum(piece["area"] for piece in pieces)
        waste_area = total_area - pieces_area

        # Вычислить геометрию областей отходов
        if waste_area > 0:
            waste_areas.append(
                {
                    "area": waste_area,
                    "percentage": (waste_area / total_area) * 100,
                    "geometry": self._calculate_waste_geometry(
                        pieces, dxf_data.dimensions
                    ),
                    "is_utilizable": waste_area > self.min_utilizable_area,
                }
            )

        return waste_areas

    def _extract_metadata(self, doc, dxf_path: Path) -> DxfMetadata:
        """
        Извлечь метаданные из DXF.

        Args:
            doc: DXF документ
            dxf_path: Путь к файлу

        Returns:
            DxfMetadata: Метаданные файла
        """
        return DxfMetadata(
            units=doc.header.get("$INSUNITS", 4),
            creation_date=doc.header.get("$TDCREATE", ""),
            last_modified=doc.header.get("$TDUPDATE", ""),
            file_path=str(dxf_path),
            file_size=dxf_path.stat().st_size,
            version=doc.dxfversion,
        )

    def _parse_entities(self, msp) -> List[DxfEntity]:
        """
        Распарсить все сущности из модели.

        Args:
            msp: Modelspace DXF документа

        Returns:
            List[DxfEntity]: Список сущностей
        """
        entities = []

        for entity in msp:
            entity_data = {
                "type": entity.dxftype(),
                "handle": entity.dxf.handle,
                "layer": entity.dxf.layer,
                "color": entity.dxf.color,
                "linetype": entity.dxf.linetype,
            }

            # Обработка различных типов сущностей
            if entity.dxftype() in ["LWPOLYLINE", "POLYLINE"]:
                entity_data.update(self._parse_polyline(entity))
            elif entity.dxftype() == "CIRCLE":
                entity_data.update(self._parse_circle(entity))
            elif entity.dxftype() == "LINE":
                entity_data.update(self._parse_line(entity))

            entities.append(DxfEntity(**entity_data))

        return entities

    def _parse_polyline(self, entity) -> Dict[str, Any]:
        """Распарсить полилинию."""
        points = []
        if hasattr(entity, "get_points"):
            points = list(entity.get_points())

        # Вычислить площадь
        area = 0.0
        if len(points) > 2:
            area = calculate_area(points)

        # Вычислить bounding box
        if points:
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            bounding_box = [
                min(x_coords),
                min(y_coords),
                max(x_coords),
                max(y_coords),
            ]
        else:
            bounding_box = [0, 0, 0, 0]

        return {"points": points, "area": area, "bounding_box": bounding_box}

    def _parse_circle(self, entity) -> Dict[str, Any]:
        """Распарсить окружность."""
        center = entity.dxf.center
        radius = entity.dxf.radius

        # Вычислить площадь
        area = np.pi * radius**2

        # Вычислить bounding box
        bounding_box = [
            center[0] - radius,
            center[1] - radius,
            center[0] + radius,
            center[1] + radius,
        ]

        return {
            "points": [[center[0], center[1], radius]],
            "area": area,
            "bounding_box": bounding_box,
        }

    def _parse_line(self, entity) -> Dict[str, Any]:
        """Распарсить линию."""
        start = entity.dxf.start
        end = entity.dxf.end

        points = [list(start), list(end)]

        # Линия не имеет площади
        return {
            "points": points,
            "area": 0.0,
            "bounding_box": [
                min(start[0], end[0]),
                min(start[1], end[1]),
                max(start[0], end[0]),
                max(start[1], end[1]),
            ],
        }

    def _get_dimensions(self, msp) -> Dict[str, float]:
        """Получить размеры листа."""
        # Найти границы всех сущностей
        all_points = []

        for entity in msp:
            if hasattr(entity, "get_points"):
                points = list(entity.get_points())
                all_points.extend(points)
            elif hasattr(entity, "dxf") and hasattr(entity.dxf, "center"):
                # Для окружностей
                center = entity.dxf.center
                radius = entity.dxf.radius
                all_points.extend(
                    [
                        [center[0] - radius, center[1] - radius],
                        [center[0] + radius, center[1] + radius],
                    ]
                )

        if all_points:
            x_coords = [p[0] for p in all_points]
            y_coords = [p[1] for p in all_points]

            return {
                "width": max(x_coords) - min(x_coords),
                "height": max(y_coords) - min(y_coords),
                "min_x": min(x_coords),
                "min_y": min(y_coords),
                "max_x": max(x_coords),
                "max_y": max(y_coords),
            }

        return {
            "width": 0,
            "height": 0,
            "min_x": 0,
            "min_y": 0,
            "max_x": 0,
            "max_y": 0,
        }

    def _extract_material_info(self, doc) -> Dict[str, Any]:
        """Извлечь информацию о материале."""
        # Ищем информацию в слоях или блоках
        material_info = {
            "thickness": 16.0,  # По умолчанию
            "material_type": "MDF",
            "density": 750.0,
        }

        # Попробуем найти информацию в слоях
        try:
            for layer in doc.layers:
                layer_name = layer.dxf.name.lower()
                if "thickness" in layer_name:
                    try:
                        thickness = float(layer_name.split("_")[-1])
                        material_info["thickness"] = thickness
                    except ValueError:
                        pass
        except (AttributeError, TypeError):
            # Если слои недоступны, используем значения по умолчанию
            pass

        return material_info

    def _calculate_statistics(
        self, entities: List[DxfEntity], dimensions: Dict[str, float]
    ) -> DxfStatistics:
        """Вычислить статистику использования материала."""
        total_area = dimensions.get("width", 0) * dimensions.get("height", 0)
        pieces_count = len(
            [
                e
                for e in entities
                if e.type in ["LWPOLYLINE", "POLYLINE", "CIRCLE"]
            ]
        )
        pieces_area = sum(e.area for e in entities)

        waste_percentage = (
            ((total_area - pieces_area) / total_area * 100)
            if total_area > 0
            else 0
        )
        average_piece_area = (
            pieces_area / pieces_count if pieces_count > 0 else 0
        )

        return DxfStatistics(
            total_area=total_area,
            pieces_count=pieces_count,
            waste_percentage=waste_percentage,
            average_piece_area=average_piece_area,
            total_cuts=len([e for e in entities if e.type == "LINE"]),
            material_usage=pieces_area,
        )

    def _calculate_waste_geometry(
        self, pieces: List[Dict], dimensions: Dict[str, float]
    ) -> List[List[float]]:
        """Вычислить геометрию областей отходов."""
        # Упрощенная реализация - возвращаем пустую геометрию
        # В реальной реализации здесь может быть сложный алгоритм
        return []

    def _get_minimum_utilizable_area(self) -> float:
        """Получить минимальную площадь, которая может быть использована."""
        try:
            return self.config._configs["base_config"]["optimization"].get(
                "min_waste_area", 100.0
            )
        except (KeyError, AttributeError):
            return 100.0  # По умолчанию 100 мм²
