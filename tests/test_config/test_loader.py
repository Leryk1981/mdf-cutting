"""
Тесты для загрузчика конфигурации.
"""

import pytest
from pathlib import Path
from src.mdf_cutting.config.loader import ConfigLoader
from src.mdf_cutting.config import TableFormat, OptimizationRule


class TestConfigLoader:
    """Тесты для ConfigLoader."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.config_dir = Path(__file__).parent.parent.parent / "src" / "mdf_cutting" / "config"
        self.loader = ConfigLoader(self.config_dir)

    def test_load_all_configs(self):
        """Тест загрузки всех конфигураций."""
        self.loader.load_all()
        assert "base_config" in self.loader._configs
        assert "production_tables" in self.loader._configs
        assert "optimization_rules" in self.loader._configs
        assert self.loader._loaded is True

    def test_table_format_parsing(self):
        """Тест парсинга форматов таблиц."""
        table_format = self.loader.get_table_format("standard_table")
        assert table_format is not None
        assert table_format.id == "standard_table"
        assert len(table_format.columns) > 0
        
        # Проверяем что формат таблиц не изменен
        expected_columns = ["material_code", "length", "width", "quantity"]
        actual_columns = [col.name for col in table_format.columns]
        assert all(col in actual_columns for col in expected_columns)

    def test_optimization_rules(self):
        """Тест загрузки правил оптимизации."""
        rules = self.loader.get_optimization_rules("mdf_16mm")
        assert len(rules) > 0
        assert all(rule.min_spacing > 0 for rule in rules)
        assert all(rule.max_cuts > 0 for rule in rules)
        assert all(len(rule.material_types) > 0 for rule in rules)

    def test_get_config(self):
        """Тест получения конфигурации по имени."""
        config = self.loader.get_config("base_config")
        assert "optimization" in config
        assert "material" in config
        assert "logging" in config

    def test_list_table_formats(self):
        """Тест получения списка форматов таблиц."""
        formats = self.loader.list_table_formats()
        assert "standard_table" in formats
        assert "customer_legacy_table" in formats
        assert "materials_table" in formats

    def test_list_material_types(self):
        """Тест получения списка типов материалов."""
        material_types = self.loader.list_material_types()
        assert "mdf_16mm" in material_types
        assert "mdf_18mm" in material_types
        assert "mdf_12mm" in material_types

    def test_reload_config(self):
        """Тест перезагрузки конфигурации."""
        self.loader.load_all()
        initial_configs = len(self.loader._configs)
        
        self.loader.reload()
        assert len(self.loader._configs) == initial_configs
        assert self.loader._loaded is True

    def test_invalid_config_dir(self):
        """Тест обработки несуществующей директории."""
        invalid_dir = Path("/nonexistent/path")
        loader = ConfigLoader(invalid_dir)
        
        with pytest.raises(RuntimeError):
            loader.load_all()

    def test_missing_table_format(self):
        """Тест получения несуществующего формата таблицы."""
        table_format = self.loader.get_table_format("nonexistent_format")
        assert table_format is None 