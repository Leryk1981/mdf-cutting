"""
Конфигурационная система для MDF Cutting.

Этот модуль содержит:
- Типы данных для конфигурации
- Интерфейсы для загрузки конфигурации
- Валидацию конфигурационных параметров
- Поддержку стандартных форматов таблиц заказчика
"""

from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel, validator


class TableColumn(BaseModel):
    """Структура столбца таблицы."""

    name: str
    type: str
    required: Union[bool, str] = False
    description: Optional[str] = None


class TableFormat(BaseModel):
    """Стандартный формат таблиц заказчика"""

    id: str
    name: str
    columns: List[TableColumn]
    delimiter: str
    encoding: str = "utf-8"

    @validator("columns")
    def validate_columns(cls, v):
        """Валидация формата столбцов без изменения стандарта"""
        if not v:
            raise ValueError("Columns cannot be empty")
        return v

    @validator("id")
    def validate_id(cls, v):
        """Валидация ID формата"""
        if not v or not v.strip():
            raise ValueError("ID cannot be empty")
        return v.strip()


class OptimizationRule(BaseModel):
    """Правило оптимизации для конкретного производства"""

    name: str
    min_spacing: float
    max_cuts: int
    material_types: List[str]
    priority: int = 1
    description: Optional[str] = None

    @validator("min_spacing")
    def validate_min_spacing(cls, v):
        """Валидация минимального отступа"""
        if v <= 0:
            raise ValueError("min_spacing must be positive")
        return v

    @validator("max_cuts")
    def validate_max_cuts(cls, v):
        """Валидация максимального количества резов"""
        if v <= 0:
            raise ValueError("max_cuts must be positive")
        return v

    @validator("material_types")
    def validate_material_types(cls, v):
        """Валидация типов материалов"""
        if not v:
            raise ValueError("material_types cannot be empty")
        return v


class ConfigManager(BaseModel):
    """Менеджер конфигурации с поддержкой переменных окружения"""

    env_file: str = ".env"
    table_format_id: str = "standard_table"
    debug_mode: bool = False
    config_path: Optional[Path] = None

    @validator("table_format_id")
    def validate_table_format_id(cls, v):
        """Валидация ID формата таблицы"""
        if not v or not v.strip():
            raise ValueError("table_format_id cannot be empty")
        return v.strip()


# Экспорт основных типов
__all__ = ["TableFormat", "TableColumn", "OptimizationRule", "ConfigManager"]
