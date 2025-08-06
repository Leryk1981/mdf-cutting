"""
Тесты для модуля core.

Тестирует основные алгоритмы упаковки и оптимизации.
"""

import pytest

from src.mdf_cutting.core.optimizer import CuttingOptimizer


class TestCuttingOptimizer:
    """Тесты для основного оптимизатора."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.optimizer = CuttingOptimizer()

    def test_initialization(self):
        """Тест инициализации оптимизатора."""
        assert self.optimizer is not None
        assert hasattr(self.optimizer, "data_manager")
        assert hasattr(self.optimizer, "packing_algorithm")
        assert hasattr(self.optimizer, "dxf_generator")
        assert hasattr(self.optimizer, "remnants_manager")

    def test_optimize_cutting_empty_data(self):
        """Тест оптимизации с пустыми данными."""
        # Создаем пустые данные без pandas
        empty_data = {}
        result = self.optimizer.optimize_cutting(empty_data, empty_data)
        assert result is not None

    def test_generate_dxf_files(self):
        """Тест генерации DXF файлов."""
        optimization_results = {"test": "data"}
        result = self.optimizer.generate_dxf_files(optimization_results)
        assert isinstance(result, list)

    def test_update_remnants(self):
        """Тест обновления остатков."""
        optimization_results = {"test": "data"}
        result = self.optimizer.update_remnants(optimization_results)
        assert result is not None
