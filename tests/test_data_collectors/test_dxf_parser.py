"""
Тесты для DXF парсера.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.mdf_cutting.config.loader import ConfigLoader
from src.mdf_cutting.data_collectors.dxf_parser import DxfParser


class TestDxfParser:
    """Тесты для DxfParser."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.config_loader = Mock(spec=ConfigLoader)
        self.config_loader._configs = {
            "base_config": {"optimization": {"min_waste_area": 100.0}}
        }
        self.parser = DxfParser(self.config_loader)

    def test_initialization(self):
        """Тест инициализации парсера."""
        assert self.parser.config is not None
        assert self.parser.min_utilizable_area == 100.0

    def test_get_minimum_utilizable_area(self):
        """Тест получения минимальной площади."""
        area = self.parser._get_minimum_utilizable_area()
        assert area == 100.0

    def test_get_minimum_utilizable_area_fallback(self):
        """Тест получения минимальной площади при отсутствии конфигурации."""
        self.config_loader._configs = {}
        area = self.parser._get_minimum_utilizable_area()
        assert area == 100.0

    @patch("ezdxf.readfile")
    def test_parse_cutting_map_success(self, mock_readfile):
        """Тест успешного парсинга DXF файла."""
        # Мокаем DXF документ
        mock_doc = Mock()
        mock_doc.header = {
            "$INSUNITS": 4,
            "$TDCREATE": "2023-01-01",
            "$TDUPDATE": "2023-01-02",
        }
        mock_doc.dxfversion = "R2010"

        mock_msp = Mock()
        mock_msp.__iter__ = lambda self: iter([])

        mock_doc.modelspace.return_value = mock_msp
        mock_readfile.return_value = mock_doc

        # Создаем временный файл
        test_file = Path("test.dxf")
        test_file.touch()

        try:
            result = self.parser.parse_cutting_map(test_file)

            assert result.metadata.units == 4
            assert result.metadata.version == "R2010"
            assert len(result.entities) == 0
            assert result.statistics.total_area == 0
        finally:
            test_file.unlink(missing_ok=True)

    def test_parse_cutting_map_file_not_found(self):
        """Тест обработки несуществующего файла."""
        with pytest.raises(ValueError, match="Не удалось прочитать DXF файл"):
            self.parser.parse_cutting_map(Path("nonexistent.dxf"))

    def test_extract_raw_pieces_empty(self):
        """Тест извлечения заготовок из пустых данных."""
        from src.mdf_cutting.data_collectors.schemas import (
            DxfData,
            DxfEntity,
            DxfMetadata,
            DxfStatistics,
        )

        # Создаем пустые данные
        empty_data = DxfData(
            metadata=DxfMetadata(
                units=4, file_path="test.dxf", file_size=0, version="R2010"
            ),
            entities=[],
            statistics=DxfStatistics(
                total_area=0,
                pieces_count=0,
                waste_percentage=0,
                average_piece_area=0,
                total_cuts=0,
                material_usage=0,
            ),
            dimensions={},
            material_info={},
        )

        pieces = self.parser.extract_raw_pieces(empty_data)
        assert len(pieces) == 0

    def test_extract_waste_areas_empty(self):
        """Тест определения областей отходов для пустых данных."""
        from src.mdf_cutting.data_collectors.schemas import (
            DxfData,
            DxfEntity,
            DxfMetadata,
            DxfStatistics,
        )

        # Создаем данные без деталей
        empty_data = DxfData(
            metadata=DxfMetadata(
                units=4, file_path="test.dxf", file_size=0, version="R2010"
            ),
            entities=[],
            statistics=DxfStatistics(
                total_area=1000,  # Площадь листа
                pieces_count=0,
                waste_percentage=100,
                average_piece_area=0,
                total_cuts=0,
                material_usage=0,
            ),
            dimensions={"width": 100, "height": 10},
            material_info={},
        )

        waste_areas = self.parser.extract_waste_areas(empty_data)
        assert len(waste_areas) == 1
        assert waste_areas[0]["area"] == 1000
        assert waste_areas[0]["percentage"] == 100.0

    def test_parse_polyline(self):
        """Тест парсинга полилинии."""
        mock_entity = Mock()
        mock_entity.dxftype.return_value = "LWPOLYLINE"
        mock_entity.dxf.handle = "123"
        mock_entity.dxf.layer = "CUT"
        mock_entity.dxf.color = 7
        mock_entity.dxf.linetype = "CONTINUOUS"
        mock_entity.get_points.return_value = [
            (0, 0),
            (10, 0),
            (10, 10),
            (0, 10),
        ]

        result = self.parser._parse_polyline(mock_entity)

        assert len(result["points"]) == 4
        # Площадь вычисляется по формуле шнурка для прямоугольника 10x10
        assert result["area"] == 100.0
        assert len(result["bounding_box"]) == 4

    def test_parse_circle(self):
        """Тест парсинга окружности."""
        mock_entity = Mock()
        mock_entity.dxftype.return_value = "CIRCLE"
        mock_entity.dxf.handle = "456"
        mock_entity.dxf.layer = "CUT"
        mock_entity.dxf.color = 7
        mock_entity.dxf.linetype = "CONTINUOUS"
        mock_entity.dxf.center = (5, 5)
        mock_entity.dxf.radius = 3

        result = self.parser._parse_circle(mock_entity)

        assert len(result["points"]) == 1
        assert result["area"] == pytest.approx(np.pi * 9, rel=1e-6)
        assert len(result["bounding_box"]) == 4

    def test_parse_line(self):
        """Тест парсинга линии."""
        mock_entity = Mock()
        mock_entity.dxftype.return_value = "LINE"
        mock_entity.dxf.handle = "789"
        mock_entity.dxf.layer = "CUT"
        mock_entity.dxf.color = 7
        mock_entity.dxf.linetype = "CONTINUOUS"
        mock_entity.dxf.start = (0, 0)
        mock_entity.dxf.end = (10, 10)

        result = self.parser._parse_line(mock_entity)

        assert len(result["points"]) == 2
        assert result["area"] == 0.0  # Линия не имеет площади
        assert len(result["bounding_box"]) == 4

    def test_get_dimensions_empty(self):
        """Тест получения размеров для пустых данных."""
        mock_msp = Mock()
        mock_msp.__iter__ = lambda self: iter([])

        dimensions = self.parser._get_dimensions(mock_msp)

        assert dimensions["width"] == 0
        assert dimensions["height"] == 0

    def test_extract_material_info(self):
        """Тест извлечения информации о материале."""
        mock_doc = Mock()
        mock_layer = Mock()
        mock_layer.dxf.name = "MDF_16mm"

        mock_doc.layers = [mock_layer]

        material_info = self.parser._extract_material_info(mock_doc)

        assert material_info["thickness"] == 16.0
        assert material_info["material_type"] == "MDF"
        assert material_info["density"] == 750.0
