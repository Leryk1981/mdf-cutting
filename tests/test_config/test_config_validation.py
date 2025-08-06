"""
Тесты валидации конфигурации.
"""

import pytest
from pydantic import ValidationError
from src.mdf_cutting.config import TableFormat, OptimizationRule, ConfigManager


class TestTableFormatValidation:
    """Тесты валидации форматов таблиц."""

    def test_valid_table_format(self):
        """Тест валидного формата таблицы."""
        valid_data = {
            "id": "test_format",
            "name": "Test Format",
            "columns": [
                {"name": "col1", "type": "str", "required": True}
            ],
            "delimiter": ";"
        }
        table_format = TableFormat(**valid_data)
        assert table_format.id == "test_format"
        assert len(table_format.columns) == 1

    def test_invalid_empty_id(self):
        """Тест невалидного пустого ID."""
        invalid_data = {
            "id": "",
            "name": "Test Format",
            "columns": [
                {"name": "col1", "type": "str", "required": True}
            ],
            "delimiter": ";"
        }
        with pytest.raises(ValidationError):
            TableFormat(**invalid_data)

    def test_invalid_empty_columns(self):
        """Тест невалидных пустых столбцов."""
        invalid_data = {
            "id": "test_format",
            "name": "Test Format",
            "columns": [],
            "delimiter": ";"
        }
        with pytest.raises(ValidationError):
            TableFormat(**invalid_data)

    def test_default_encoding(self):
        """Тест значения по умолчанию для encoding."""
        data = {
            "id": "test_format",
            "name": "Test Format",
            "columns": [
                {"name": "col1", "type": "str", "required": True}
            ],
            "delimiter": ";"
        }
        table_format = TableFormat(**data)
        assert table_format.encoding == "utf-8"


class TestOptimizationRuleValidation:
    """Тесты валидации правил оптимизации."""

    def test_valid_optimization_rule(self):
        """Тест валидного правила оптимизации."""
        valid_data = {
            "name": "test_rule",
            "min_spacing": 5.0,
            "max_cuts": 50,
            "material_types": ["MDF", "LDPE"]
        }
        rule = OptimizationRule(**valid_data)
        assert rule.name == "test_rule"
        assert rule.min_spacing == 5.0
        assert rule.priority == 1  # значение по умолчанию

    def test_invalid_negative_min_spacing(self):
        """Тест невалидного отрицательного min_spacing."""
        invalid_data = {
            "name": "test_rule",
            "min_spacing": -1.0,
            "max_cuts": 50,
            "material_types": ["MDF"]
        }
        with pytest.raises(ValidationError):
            OptimizationRule(**invalid_data)

    def test_invalid_zero_max_cuts(self):
        """Тест невалидного нулевого max_cuts."""
        invalid_data = {
            "name": "test_rule",
            "min_spacing": 5.0,
            "max_cuts": 0,
            "material_types": ["MDF"]
        }
        with pytest.raises(ValidationError):
            OptimizationRule(**invalid_data)

    def test_invalid_empty_material_types(self):
        """Тест невалидных пустых типов материалов."""
        invalid_data = {
            "name": "test_rule",
            "min_spacing": 5.0,
            "max_cuts": 50,
            "material_types": []
        }
        with pytest.raises(ValidationError):
            OptimizationRule(**invalid_data)

    def test_custom_priority(self):
        """Тест пользовательского приоритета."""
        data = {
            "name": "test_rule",
            "min_spacing": 5.0,
            "max_cuts": 50,
            "material_types": ["MDF"],
            "priority": 5
        }
        rule = OptimizationRule(**data)
        assert rule.priority == 5


class TestConfigManagerValidation:
    """Тесты валидации менеджера конфигурации."""

    def test_valid_config_manager(self):
        """Тест валидного менеджера конфигурации."""
        valid_data = {
            "table_format_id": "standard_table",
            "debug_mode": True
        }
        config = ConfigManager(**valid_data)
        assert config.table_format_id == "standard_table"
        assert config.debug_mode is True
        assert config.env_file == ".env"  # значение по умолчанию

    def test_invalid_empty_table_format_id(self):
        """Тест невалидного пустого table_format_id."""
        invalid_data = {
            "table_format_id": "",
            "debug_mode": False
        }
        with pytest.raises(ValidationError):
            ConfigManager(**invalid_data)

    def test_whitespace_stripping(self):
        """Тест удаления пробелов из ID."""
        data = {
            "table_format_id": "  test_format  ",
            "debug_mode": False
        }
        config = ConfigManager(**data)
        assert config.table_format_id == "test_format" 