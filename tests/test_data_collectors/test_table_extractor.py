"""
Тесты для извлекателя табличных данных.
"""

from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

pytest.importorskip("torch")

from src.mdf_cutting.config import TableColumn, TableFormat
from src.mdf_cutting.config.loader import ConfigLoader
from src.mdf_cutting.data_collectors.table_extractor import TableDataExtractor


class TestTableDataExtractor:
    """Тесты для TableDataExtractor."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.config_loader = Mock(spec=ConfigLoader)

        # Мокаем формат таблицы
        table_format = TableFormat(
            id="standard_table",
            name="Стандартная таблица",
            delimiter=";",
            encoding="utf-8",
            columns=[
                TableColumn(name="material_code", type="str", required=True),
                TableColumn(name="length", type="float", required=True),
                TableColumn(name="width", type="float", required=True),
                TableColumn(name="quantity", type="int", required=False),
                TableColumn(name="thickness", type="float", required=True),
                TableColumn(name="material", type="str", required=True),
            ],
        )

        self.config_loader.get_table_format.return_value = table_format
        self.config_loader._configs = {
            "production_tables": {
                "material_thickness": {"MDF_16": 16.0, "MDF_18": 18.0},
                "material_properties": {
                    "MDF_16": {
                        "thickness": 16.0,
                        "density": 750.0,
                        "quality_factor": 1.0,
                        "material_type": "MDF",
                        "cost_per_sqm": 500.0,
                    }
                },
            }
        }

        self.extractor = TableDataExtractor(self.config_loader)

    def test_initialization(self):
        """Тест инициализации извлекателя."""
        assert self.extractor.config is not None

    def test_extract_order_data_success(self):
        """Тест успешного извлечения данных заказа."""
        # Создаем временный CSV файл
        test_data = pd.DataFrame(
            {
                "material_code": ["MDF_16", "MDF_18"],
                "length": ["100", "200"],
                "width": ["50", "75"],
                "quantity": ["2", "1"],
                "thickness": ["16", "18"],
                "material": ["MDF", "MDF"],
            }
        )

        test_file = Path("test_orders.csv")
        test_data.to_csv(test_file, sep=";", index=False)

        try:
            orders = self.extractor.extract_order_data(
                test_file, "standard_table"
            )

            assert len(orders) == 2
            assert orders[0].material_code == "MDF_16"
            assert orders[0].length == 100.0
            assert orders[0].width == 50.0
            assert orders[0].quantity == 2
            assert orders[0].thickness == 16.0
        finally:
            test_file.unlink(missing_ok=True)

    def test_extract_order_data_unknown_format(self):
        """Тест обработки неизвестного формата таблицы."""
        self.config_loader.get_table_format.return_value = None

        with pytest.raises(ValueError, match="Неизвестный формат таблицы"):
            self.extractor.extract_order_data(
                Path("test.csv"), "unknown_format"
            )

    def test_extract_order_data_file_not_found(self):
        """Тест обработки несуществующего файла."""
        with pytest.raises(ValueError, match="Не удалось прочитать таблицу"):
            self.extractor.extract_order_data(
                Path("nonexistent.csv"), "standard_table"
            )

    def test_extract_correction_journal_csv(self):
        """Тест извлечения журнала корректировок из CSV."""
        test_data = pd.DataFrame(
            {
                "dxf_file": ["test1.dxf", "test2.dxf"],
                "timestamp": ["2023-01-01 10:00:00", "2023-01-02 11:00:00"],
                "correction_type": ["position", "rotation"],
                "affected_pieces": ["piece1;piece2", "piece3"],
                "reason": ["Improvement", "Optimization"],
                "operator": ["operator1", "operator2"],
                "improvement_score": ["0.8", "0.6"],
            }
        )

        test_file = Path("test_corrections.csv")
        test_data.to_csv(test_file, index=False)

        try:
            corrections = self.extractor.extract_correction_journal(test_file)

            assert len(corrections) == 2
            assert corrections[0].dxf_file == "test1.dxf"
            assert corrections[0].correction_type == "position"
            assert corrections[0].affected_pieces == ["piece1", "piece2"]
            assert corrections[0].operator == "operator1"
            assert corrections[0].improvement_score == 0.8
        finally:
            test_file.unlink(missing_ok=True)

    def test_extract_material_properties(self):
        """Тест извлечения свойств материала."""
        properties = self.extractor.extract_material_properties("MDF_16")

        assert properties.thickness == 16.0
        assert properties.density == 750.0
        assert properties.quality_factor == 1.0
        assert properties.material_type == "MDF"
        assert properties.cost_per_sqm == 500.0

    def test_validate_table_format_success(self):
        """Тест успешной валидации формата таблицы."""
        test_data = pd.DataFrame(
            {
                "material_code": ["MDF_16"],
                "length": ["100"],
                "width": ["50"],
                "thickness": ["16"],
                "material": ["MDF"],
            }
        )

        test_file = Path("test_validation.csv")
        test_data.to_csv(test_file, sep=";", index=False)

        try:
            is_valid = self.extractor.validate_table_format(
                test_file, "standard_table"
            )
            assert is_valid is True
        finally:
            test_file.unlink(missing_ok=True)

    def test_validate_table_format_missing_columns(self):
        """Тест валидации таблицы с отсутствующими колонками."""
        test_data = pd.DataFrame(
            {
                "material_code": ["MDF_16"],
                "length": ["100"],
                # Отсутствуют обязательные колонки width, thickness, material
            }
        )

        test_file = Path("test_invalid.csv")
        test_data.to_csv(test_file, sep=";", index=False)

        try:
            is_valid = self.extractor.validate_table_format(
                test_file, "standard_table"
            )
            assert is_valid is False
        finally:
            test_file.unlink(missing_ok=True)

    def test_safe_float_valid(self):
        """Тест безопасного преобразования в float."""
        assert self.extractor._safe_float("123.45") == 123.45
        assert (
            self.extractor._safe_float("123,45") == 123.45
        )  # Европейский формат
        assert self.extractor._safe_float(123.45) == 123.45
        assert self.extractor._safe_float(None) == 0.0
        assert self.extractor._safe_float("") == 0.0

    def test_safe_float_invalid(self):
        """Тест безопасного преобразования в float для невалидных значений."""
        assert self.extractor._safe_float("invalid") == 0.0
        assert self.extractor._safe_float("abc") == 0.0

    def test_safe_int_valid(self):
        """Тест безопасного преобразования в int."""
        assert self.extractor._safe_int("123") == 123
        assert self.extractor._safe_int(123.45) == 123
        assert self.extractor._safe_int(None) == 1
        assert self.extractor._safe_int("") == 1

    def test_safe_int_invalid(self):
        """Тест безопасного преобразования в int для невалидных значений."""
        assert self.extractor._safe_int("invalid") == 1
        assert self.extractor._safe_int("abc") == 1

    def test_get_thickness_from_material_code(self):
        """Тест определения толщины по коду материала."""
        assert self.extractor._get_thickness_from_material("MDF_16") == 16.0
        assert self.extractor._get_thickness_from_material("MDF_18") == 18.0
        assert (
            self.extractor._get_thickness_from_material("unknown") == 16.0
        )  # По умолчанию

    def test_get_thickness_from_material_code_invalid(self):
        """Тест определения толщины для невалидного кода."""
        assert (
            self.extractor._get_thickness_from_material("MDF_invalid") == 16.0
        )  # По умолчанию
        assert (
            self.extractor._get_thickness_from_material("") == 16.0
        )  # По умолчанию

    def test_parse_affected_pieces_semicolon(self):
        """Тест парсинга затронутых деталей с разделителем ';'."""
        pieces = self.extractor._parse_affected_pieces("piece1;piece2;piece3")
        assert pieces == ["piece1", "piece2", "piece3"]

    def test_parse_affected_pieces_comma(self):
        """Тест парсинга затронутых деталей с разделителем ','."""
        pieces = self.extractor._parse_affected_pieces("piece1,piece2,piece3")
        assert pieces == ["piece1", "piece2", "piece3"]

    def test_parse_affected_pieces_pipe(self):
        """Тест парсинга затронутых деталей с разделителем '|'."""
        pieces = self.extractor._parse_affected_pieces("piece1|piece2|piece3")
        assert pieces == ["piece1", "piece2", "piece3"]

    def test_parse_affected_pieces_single(self):
        """Тест парсинга одной детали без разделителя."""
        pieces = self.extractor._parse_affected_pieces("piece1")
        assert pieces == ["piece1"]

    def test_parse_affected_pieces_empty(self):
        """Тест парсинга пустого списка деталей."""
        pieces = self.extractor._parse_affected_pieces("")
        assert pieces == []

        pieces = self.extractor._parse_affected_pieces(None)
        assert pieces == []
