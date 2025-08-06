"""
Тесты для сериализатора данных ML.
"""

import json
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np
import pytest

from src.mdf_cutting.data_collectors.data_serializer import (
    MLDataSerializer,
    NumpyEncoder,
)


class TestMLDataSerializer:
    """Тесты для MLDataSerializer."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.test_dir = Path("test_output")
        self.test_dir.mkdir(exist_ok=True)
        self.serializer = MLDataSerializer(self.test_dir)

    def teardown_method(self):
        """Очистка после каждого теста."""
        import shutil

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Тест инициализации сериализатора."""
        assert self.serializer.output_dir == self.test_dir
        assert self.test_dir.exists()

    def test_serialize_training_batch(self):
        """Тест сериализации партии данных для обучения."""
        # Создаем тестовые данные
        test_data = [
            {
                "order_data": {
                    "material_code": "MDF_16",
                    "length": 100.0,
                    "width": 50.0,
                    "quantity": 2,
                    "thickness": 16.0,
                },
                "dxf_data": {
                    "total_area": 5000.0,
                    "pieces_count": 5,
                    "waste_percentage": 15.0,
                    "average_piece_area": 850.0,
                    "total_cuts": 12,
                    "material_usage": 4250.0,
                },
                "material_data": {
                    "thickness": 16.0,
                    "density": 750.0,
                    "quality_factor": 1.0,
                    "material_type": "MDF",
                    "cost_per_sqm": 500.0,
                },
                "corrections": [0.1, 0.2, 0.3],
                "waste_reduction": 0.15,
                "layout_score": 0.85,
            }
        ]

        batch_id = "test_batch_001"
        output_path = self.serializer.serialize_training_batch(
            test_data, batch_id
        )

        assert output_path.exists()
        assert output_path.name == f"training_batch_{batch_id}.h5"

        # Проверяем содержимое файла
        with h5py.File(output_path, "r") as f:
            assert "metadata" in f
            assert "samples" in f
            assert f["metadata"].attrs["batch_id"] == batch_id
            assert f["metadata"].attrs["total_samples"] == 1

    def test_serialize_real_time_data(self):
        """Тест сериализации данных в реальном времени."""
        test_data = {
            "order_info": [12345, 100.0, 50.0, 2, 16.0],
            "dxf_geometry": [5000.0, 5, 15.0, 850.0],
            "material_properties": [16.0, 750.0, 1.0],
            "timestamp": datetime.now(),
        }

        output_path = self.serializer.serialize_real_time_data(test_data)

        assert output_path.exists()
        assert output_path.name.startswith("realtime_")
        assert output_path.suffix == ".json"

        # Проверяем содержимое файла
        with open(output_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
            assert "order_info" in loaded_data
            assert "dxf_geometry" in loaded_data
            assert "material_properties" in loaded_data

    def test_serialize_corrections_dataset(self):
        """Тест сериализации набора данных корректировок."""
        corrections = [
            {
                "dxf_file": "test1.dxf",
                "timestamp": datetime.now().isoformat(),
                "correction_type": "position",
                "affected_pieces": ["piece1", "piece2"],
                "reason": "Optimization",
                "operator": "operator1",
                "improvement_score": 0.8,
            },
            {
                "dxf_file": "test2.dxf",
                "timestamp": datetime.now().isoformat(),
                "correction_type": "rotation",
                "affected_pieces": ["piece3"],
                "reason": "Better fit",
                "operator": "operator2",
                "improvement_score": 0.6,
            },
        ]

        dataset_id = "test_dataset_001"
        output_path = self.serializer.serialize_corrections_dataset(
            corrections, dataset_id
        )

        assert output_path.exists()
        assert output_path.name == f"corrections_dataset_{dataset_id}.json"

        # Проверяем содержимое файла
        with open(output_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
            assert loaded_data["dataset_id"] == dataset_id
            assert loaded_data["total_corrections"] == 2
            assert len(loaded_data["corrections"]) == 2

    def test_load_training_batch(self):
        """Тест загрузки партии данных для обучения."""
        # Сначала создаем тестовую партию
        test_data = [
            {
                "order_data": {
                    "material_code": "MDF_16",
                    "length": 100.0,
                    "width": 50.0,
                    "quantity": 2,
                    "thickness": 16.0,
                },
                "dxf_data": {
                    "total_area": 5000.0,
                    "pieces_count": 5,
                    "waste_percentage": 15.0,
                    "average_piece_area": 850.0,
                    "total_cuts": 12,
                    "material_usage": 4250.0,
                },
                "material_data": {
                    "thickness": 16.0,
                    "density": 750.0,
                    "quality_factor": 1.0,
                    "material_type": "MDF",
                    "cost_per_sqm": 500.0,
                },
                "corrections": [0.1, 0.2, 0.3],
                "waste_reduction": 0.15,
                "layout_score": 0.85,
            }
        ]

        batch_id = "test_load_batch"
        batch_path = self.serializer.serialize_training_batch(
            test_data, batch_id
        )

        # Теперь загружаем данные
        loaded_data = self.serializer.load_training_batch(batch_path)

        assert "metadata" in loaded_data
        assert "samples" in loaded_data
        assert loaded_data["metadata"]["batch_id"] == batch_id
        assert loaded_data["metadata"]["total_samples"] == 1
        assert len(loaded_data["samples"]) == 1

    def test_load_training_batch_file_not_found(self):
        """Тест загрузки несуществующего файла партии."""
        with pytest.raises(FileNotFoundError):
            self.serializer.load_training_batch(Path("nonexistent.h5"))

    def test_get_batch_statistics(self):
        """Тест получения статистики партии данных."""
        # Создаем тестовую партию
        test_data = [
            {
                "order_data": {
                    "material_code": "MDF_16",
                    "length": 100.0,
                    "width": 50.0,
                    "quantity": 2,
                    "thickness": 16.0,
                },
                "dxf_data": {
                    "total_area": 5000.0,
                    "pieces_count": 5,
                    "waste_percentage": 15.0,
                    "average_piece_area": 850.0,
                    "total_cuts": 12,
                    "material_usage": 4250.0,
                },
                "material_data": {
                    "thickness": 16.0,
                    "density": 750.0,
                    "quality_factor": 1.0,
                    "material_type": "MDF",
                    "cost_per_sqm": 500.0,
                },
                "corrections": [0.1, 0.2, 0.3],
                "waste_reduction": 0.15,
                "layout_score": 0.85,
            },
            {
                "order_data": {
                    "material_code": "MDF_18",
                    "length": 200.0,
                    "width": 75.0,
                    "quantity": 1,
                    "thickness": 18.0,
                },
                "dxf_data": {
                    "total_area": 8000.0,
                    "pieces_count": 8,
                    "waste_percentage": 20.0,
                    "average_piece_area": 800.0,
                    "total_cuts": 15,
                    "material_usage": 6400.0,
                },
                "material_data": {
                    "thickness": 18.0,
                    "density": 750.0,
                    "quality_factor": 1.0,
                    "material_type": "MDF",
                    "cost_per_sqm": 600.0,
                },
                "corrections": [0.2, 0.3],
                "waste_reduction": 0.20,
                "layout_score": 0.80,
            },
        ]

        batch_id = "test_stats_batch"
        batch_path = self.serializer.serialize_training_batch(
            test_data, batch_id
        )

        # Получаем статистику
        stats = self.serializer.get_batch_statistics(batch_path)

        assert "total_samples" in stats
        assert "average_waste_reduction" in stats
        assert "average_layout_score" in stats
        assert stats["total_samples"] == 2
        assert stats["average_waste_reduction"] == pytest.approx(
            0.175, rel=1e-6
        )
        assert stats["average_layout_score"] == pytest.approx(0.825, rel=1e-6)

    def test_process_order_info(self):
        """Тест обработки информации о заказе."""
        order_data = {
            "material_code": "MDF_16",
            "length": 100.0,
            "width": 50.0,
            "quantity": 2,
            "thickness": 16.0,
        }

        result = self.serializer._process_order_info(order_data)

        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32
        assert len(result) == 5
        assert result[1] == 100.0  # length
        assert result[2] == 50.0  # width
        assert result[3] == 2  # quantity
        assert result[4] == 16.0  # thickness

    def test_process_dxf_data(self):
        """Тест обработки данных DXF."""
        dxf_data = {
            "total_area": 5000.0,
            "pieces_count": 5,
            "waste_percentage": 15.0,
            "average_piece_area": 850.0,
            "total_cuts": 12,
            "material_usage": 4250.0,
        }

        result = self.serializer._process_dxf_data(dxf_data)

        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32
        assert len(result) == 6
        assert result[0] == 5000.0  # total_area
        assert result[1] == 5  # pieces_count
        assert result[2] == 15.0  # waste_percentage

    def test_process_material_data(self):
        """Тест обработки данных о материале."""
        material_data = {
            "thickness": 16.0,
            "density": 750.0,
            "quality_factor": 1.0,
            "material_type": "MDF",
            "cost_per_sqm": 500.0,
        }

        result = self.serializer._process_material_data(material_data)

        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32
        assert len(result) == 5
        assert result[0] == 16.0  # thickness
        assert result[1] == 750.0  # density
        assert result[2] == 1.0  # quality_factor

    def test_hash_string(self):
        """Тест хеширования строк."""
        assert self.serializer._hash_string("MDF_16") > 0
        assert self.serializer._hash_string("") == 0.0
        assert self.serializer._hash_string(None) == 0.0


class TestNumpyEncoder:
    """Тесты для NumpyEncoder."""

    def test_encode_numpy_array(self):
        """Тест кодирования numpy массива."""
        encoder = NumpyEncoder()
        data = np.array([1, 2, 3])
        result = encoder.default(data)
        assert result == [1, 2, 3]

    def test_encode_numpy_integer(self):
        """Тест кодирования numpy целого числа."""
        encoder = NumpyEncoder()
        data = np.int32(42)
        result = encoder.default(data)
        assert result == 42

    def test_encode_numpy_float(self):
        """Тест кодирования numpy числа с плавающей точкой."""
        encoder = NumpyEncoder()
        data = np.float64(3.14)
        result = encoder.default(data)
        assert result == 3.14

    def test_encode_datetime(self):
        """Тест кодирования datetime."""
        encoder = NumpyEncoder()
        data = datetime(2023, 1, 1, 12, 0, 0)
        result = encoder.default(data)
        assert isinstance(result, str)
        assert "2023-01-01T12:00:00" in result

    def test_encode_regular_types(self):
        """Тест кодирования обычных типов."""
        encoder = NumpyEncoder()

        # Должно вызвать TypeError для обычных типов
        with pytest.raises(TypeError):
            encoder.default("string")

        with pytest.raises(TypeError):
            encoder.default(42)
