"""
Модуль извлечения данных из таблиц заказов.

Этот модуль содержит:
- Извлечение данных из стандартных таблиц заказчика
- Парсинг журналов корректировок
- Валидацию табличных данных
- Сохранение оригинальных форматов
"""

from pathlib import Path
from typing import Any, List

import pandas as pd

from ..config.loader import ConfigLoader
from .schemas import CorrectionData, MaterialProperties, OrderData


class TableDataExtractor:
    """
    Извлекатель данных из таблиц заказов.

    Обеспечивает извлечение данных из стандартных таблиц заказчика
    с сохранением оригинальных форматов и валидацией данных.
    """

    def __init__(self, config_loader: ConfigLoader):
        """
        Инициализация извлекателя данных.

        Args:
            config_loader: Загрузчик конфигурации
        """
        self.config = config_loader
        self.config.load_all()

    def extract_order_data(
        self, table_path: Path, format_id: str
    ) -> List[OrderData]:
        """
        Извлечь данные из стандартной таблицы заказов без изменения формата.

        Args:
            table_path: Путь к таблице
            format_id: ID формата таблицы

        Returns:
            List[OrderData]: Список заказов

        Raises:
            ValueError: При ошибках чтения или неизвестном формате
        """
        table_format = self.config.get_table_format(format_id)
        if not table_format:
            raise ValueError(f"Неизвестный формат таблицы: {format_id}")

        try:
            # Читаем таблицу с сохранением стандартного формата
            df = pd.read_csv(
                table_path,
                delimiter=table_format.delimiter,
                encoding=table_format.encoding,
                dtype=str,  # Читаем все как строки для сохранения формата
            )
        except Exception as e:
            raise ValueError(f"Не удалось прочитать таблицу: {e}")

        # Преобразуем в удобный формат для обработки
        orders = []
        for _, row in df.iterrows():
            try:
                order = OrderData(
                    material_code=row.get("material_code", ""),
                    length=self._safe_float(row.get("length", 0)),
                    width=self._safe_float(row.get("width", 0)),
                    quantity=self._safe_int(row.get("quantity", 1)),
                    thickness=self._get_thickness_from_material(
                        row.get("material_code", "")
                    ),
                    raw_data=dict(row),  # Сохраняем оригинальные данные
                )
                orders.append(order)
            except Exception as e:
                # Логируем ошибку, но продолжаем обработку
                print(f"Ошибка обработки строки: {e}")
                continue

        return orders

    def extract_correction_journal(
        self, journal_path: Path
    ) -> List[CorrectionData]:
        """
        Извлечь данные из журнала ручных корректировок.

        Args:
            journal_path: Путь к журналу корректировок

        Returns:
            List[CorrectionData]: Список корректировок
        """
        try:
            # Пробуем разные форматы
            if journal_path.suffix.lower() == ".csv":
                df = pd.read_csv(journal_path)
            elif journal_path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(journal_path)
            else:
                # Пробуем CSV по умолчанию
                df = pd.read_csv(journal_path)
        except Exception as e:
            raise ValueError(f"Не удалось прочитать журнал корректировок: {e}")

        corrections = []
        for _, row in df.iterrows():
            try:
                correction = CorrectionData(
                    dxf_file=row.get("dxf_file", ""),
                    timestamp=pd.to_datetime(row.get("timestamp")),
                    correction_type=row.get("correction_type", "custom"),
                    affected_pieces=self._parse_affected_pieces(
                        row.get("affected_pieces", "")
                    ),
                    reason=row.get("reason", ""),
                    operator=row.get("operator", ""),
                    improvement_score=self._safe_float(
                        row.get("improvement_score", 0)
                    ),
                )
                corrections.append(correction)
            except Exception as e:
                print(f"Ошибка обработки корректировки: {e}")
                continue

        return corrections

    def extract_material_properties(
        self, material_code: str
    ) -> MaterialProperties:
        """
        Извлечь свойства материала по коду.

        Args:
            material_code: Код материала

        Returns:
            MaterialProperties: Свойства материала
        """
        # Используем правила из конфигурации
        material_rules = self.config._configs.get("production_tables", {}).get(
            "material_properties", {}
        )

        # Получаем свойства по коду материала
        material_data = material_rules.get(material_code, {})

        return MaterialProperties(
            thickness=material_data.get("thickness", 16.0),
            density=material_data.get("density", 750.0),
            quality_factor=material_data.get("quality_factor", 1.0),
            material_type=material_data.get("material_type", "MDF"),
            cost_per_sqm=material_data.get("cost_per_sqm", 0.0),
        )

    def validate_table_format(self, table_path: Path, format_id: str) -> bool:
        """
        Валидировать соответствие таблицы формату.

        Args:
            table_path: Путь к таблице
            format_id: ID формата

        Returns:
            bool: True если таблица соответствует формату
        """
        table_format = self.config.get_table_format(format_id)
        if not table_format:
            return False

        try:
            df = pd.read_csv(
                table_path,
                delimiter=table_format.delimiter,
                encoding=table_format.encoding,
                nrows=1,  # Читаем только заголовки
            )

            # Проверяем наличие обязательных колонок
            required_columns = [
                col.name for col in table_format.columns if col.required
            ]
            missing_columns = [
                col for col in required_columns if col not in df.columns
            ]

            return len(missing_columns) == 0

        except Exception:
            return False

    def _safe_float(self, value: Any) -> float:
        """
        Безопасное преобразование в float с учетом формата.

        Args:
            value: Значение для преобразования

        Returns:
            float: Преобразованное значение
        """
        if pd.isna(value) or value is None:
            return 0.0

        try:
            if isinstance(value, str):
                # Заменяем запятую на точку для европейского формата
                value = value.replace(",", ".")
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _safe_int(self, value: Any) -> int:
        """
        Безопасное преобразование в int.

        Args:
            value: Значение для преобразования

        Returns:
            int: Преобразованное значение
        """
        if pd.isna(value) or value is None:
            return 1

        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 1

    def _get_thickness_from_material(self, material_code: str) -> float:
        """
        Определить толщину по коду материала.

        Args:
            material_code: Код материала

        Returns:
            float: Толщина в мм
        """
        # Используем правила из конфигурации
        material_rules = self.config._configs.get("production_tables", {}).get(
            "material_thickness", {}
        )

        # Пытаемся извлечь толщину из кода материала
        if material_code:
            # Пример: MDF_16 -> 16
            parts = material_code.split("_")
            if len(parts) > 1:
                try:
                    thickness = float(parts[-1])
                    if 1 <= thickness <= 50:  # Разумные пределы
                        return thickness
                except ValueError:
                    pass

        # Возвращаем значение по умолчанию или из конфигурации
        return material_rules.get(material_code, 16.0)

    def _parse_affected_pieces(self, pieces_str: str) -> List[str]:
        """
        Распарсить список затронутых деталей.

        Args:
            pieces_str: Строка со списком деталей

        Returns:
            List[str]: Список ID деталей
        """
        if not pieces_str or pd.isna(pieces_str):
            return []

        # Поддерживаем разные разделители
        separators = [";", ",", "|", "\t"]
        for sep in separators:
            if sep in pieces_str:
                return [
                    piece.strip()
                    for piece in pieces_str.split(sep)
                    if piece.strip()
                ]

        # Если нет разделителей, считаем всю строку одним ID
        return [pieces_str.strip()] if pieces_str.strip() else []
