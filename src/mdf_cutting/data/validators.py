"""
Валидаторы данных для системы оптимизации раскроя.

Этот модуль содержит:
- Валидацию входных файлов CSV
- Проверку корректности данных деталей
- Валидацию параметров материалов
- Проверку технологических ограничений

TODO: Реализовать все валидаторы
"""

from typing import Dict, List


class DataValidator:
    """
    Основной класс для валидации данных.

    Проверяет корректность входных данных перед обработкой.
    """

    def __init__(self):
        """Инициализация валидатора."""
        self.errors = []
        self.warnings = []

    def validate_details(self, details_data: Dict) -> bool:
        """
        Валидация данных деталей.

        Args:
            details_data: Данные с деталями

        Returns:
            bool: True если данные корректны
        """
        # TODO: Реализовать валидацию деталей
        return True

    def validate_materials(self, materials_data: Dict) -> bool:
        """
        Валидация данных материалов.

        Args:
            materials_data: Данные с материалами

        Returns:
            bool: True если данные корректны
        """
        # TODO: Реализовать валидацию материалов
        return True

    def get_errors(self) -> List[str]:
        """Получить список ошибок валидации."""
        return self.errors

    def get_warnings(self) -> List[str]:
        """Получить список предупреждений валидации."""
        return self.warnings
