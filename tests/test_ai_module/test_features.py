"""
Тесты для системы признаков AI-модуля.
"""
import pytest
from unittest.mock import patch

pytest.importorskip("torch")

from src.mdf_cutting.ai_module.features.geometry import (
    GeometryFeatureExtractor,
)
from src.mdf_cutting.ai_module.features.material import (
    MaterialFeatureExtractor,
)
from src.mdf_cutting.ai_module.features.optimization import (
    OptimizationFeatureExtractor,
)


class TestGeometryFeatureExtractor:
    """Тесты для экстрактора геометрических признаков."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.extractor = GeometryFeatureExtractor()

        # Тестовые данные DXF
        self.test_dxf_data = {
            "entities": [
                {
                    "type": "LWPOLYLINE",
                    "points": [[0, 0], [100, 0], [100, 50], [0, 50]],
                    "handle": "test_handle_1",
                },
                {
                    "type": "CIRCLE",
                    "center": [200, 100],
                    "radius": 25,
                    "handle": "test_handle_2",
                },
            ]
        }

    def test_extract_features_success(self):
        """Тест успешного извлечения признаков."""
        features = self.extractor.extract_features(self.test_dxf_data)

        assert "global_features" in features
        assert "local_features" in features
        assert "spatial_features" in features
        assert "topological_features" in features

        # Проверяем глобальные признаки
        global_features = features["global_features"]
        assert "total_pieces" in global_features
        assert "utilization_rate" in global_features
        assert "waste_percentage" in global_features

    def test_extract_features_empty_data(self):
        """Тест извлечения признаков из пустых данных."""
        empty_data = {"entities": []}
        features = self.extractor.extract_features(empty_data)

        assert "global_features" in features
        assert features["global_features"]["total_pieces"] == 0

    def test_extract_features_invalid_entity(self):
        """Тест обработки некорректных сущностей."""
        invalid_data = {
            "entities": [
                {"type": "INVALID_TYPE", "points": [[0, 0], [100, 0]]}
            ]
        }

        features = self.extractor.extract_features(invalid_data)
        assert "global_features" in features

    @patch(
        "src.mdf_cutting.ai_module.features.geometry.SHAPELY_AVAILABLE", False
    )
    def test_extract_features_without_shapely(self):
        """Тест извлечения признаков без Shapely."""
        features = self.extractor.extract_features(self.test_dxf_data)

        assert "global_features" in features
        assert "local_features" in features


class TestOptimizationFeatureExtractor:
    """Тесты для экстрактора признаков оптимизации."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.extractor = OptimizationFeatureExtractor()

        self.test_dxf_data = {
            "entities": [
                {
                    "type": "LWPOLYLINE",
                    "points": [[0, 0], [100, 0], [100, 50], [0, 50]],
                }
            ]
        }

        self.test_order_data = {
            "material_code": "MDF16",
            "thickness": 16.0,
            "quantity": 1,
        }

    def test_extract_features_success(self):
        """Тест успешного извлечения признаков оптимизации."""
        features = self.extractor.extract_features(
            self.test_dxf_data, self.test_order_data
        )

        assert "material_thickness" in features
        assert "material_type_code" in features
        assert "total_cut_length" in features
        assert "utilization_rate" in features

    def test_extract_material_features(self):
        """Тест извлечения признаков материалов."""
        features = self.extractor._extract_material_features(
            self.test_dxf_data, self.test_order_data
        )

        assert features["material_thickness"] == 16.0
        assert features["material_type_code"] == "MDF16"
        assert features["is_mdf"] == 1
        assert features["order_quantity"] == 1

    def test_extract_cutting_features(self):
        """Тест извлечения признаков резки."""
        features = self.extractor._extract_cutting_features(self.test_dxf_data)

        assert "total_cut_length" in features
        assert "num_cut_operations" in features
        assert "complex_cut_ratio" in features

    def test_extract_efficiency_features(self):
        """Тест извлечения признаков эффективности."""
        features = self.extractor._extract_efficiency_features(
            self.test_dxf_data
        )

        assert "piece_size_variance" in features
        assert "utilization_rate" in features
        assert "waste_percentage" in features


class TestMaterialFeatureExtractor:
    """Тесты для экстрактора признаков материалов."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.extractor = MaterialFeatureExtractor()

        self.test_material_data = {
            "type": "MDF",
            "thickness": 16.0,
            "width": 2440,
            "height": 1220,
        }

        self.test_order_data = {
            "material_code": "MDF16",
            "thickness": 16.0,
            "quantity": 1,
        }

    def test_extract_features_success(self):
        """Тест успешного извлечения признаков материалов."""
        features = self.extractor.extract_features(
            self.test_material_data, self.test_order_data
        )

        assert "material_type" in features
        assert "material_thickness" in features
        assert "material_density" in features
        assert "sheet_area" in features

    def test_extract_basic_features(self):
        """Тест извлечения базовых признаков."""
        features = self.extractor._extract_basic_features(
            self.test_material_data, self.test_order_data
        )

        assert features["material_type"] == "MDF"
        assert features["material_thickness"] == 16.0
        assert features["material_density"] == 750
        assert features["is_mdf"] == 1

    def test_extract_technical_features(self):
        """Тест извлечения технических признаков."""
        features = self.extractor._extract_technical_features(
            self.test_material_data, self.test_order_data
        )

        assert "sheet_volume_m3" in features
        assert "sheet_weight_kg" in features
        assert "cutting_speed_factor" in features
        assert "surface_quality" in features

    def test_extract_processing_features(self):
        """Тест извлечения признаков обработки."""
        features = self.extractor._extract_processing_features(
            self.test_material_data, self.test_order_data
        )

        assert "feed_rate_mm_min" in features
        assert "spindle_speed_rpm" in features
        assert "estimated_processing_time_min" in features
        assert "edge_quality" in features

    def test_get_material_density(self):
        """Тест получения плотности материала."""
        density = self.extractor._get_material_density("MDF")
        assert density == 750

        density = self.extractor._get_material_density("HDF")
        assert density == 850

        density = self.extractor._get_material_density("UNKNOWN")
        assert density == 750  # Дефолтное значение

    def test_is_standard_thickness(self):
        """Тест проверки стандартной толщины."""
        assert self.extractor._is_standard_thickness(16.0, "MDF")
        assert self.extractor._is_standard_thickness(18.0, "MDF")
        assert self.extractor._is_standard_thickness(25.0, "MDF")
        assert not self.extractor._is_standard_thickness(
            7.5, "MDF"
        )  # Нестандартная толщина
