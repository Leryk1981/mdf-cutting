"""
Модуль сбора данных для AI-системы MDF Cutting.

Этот модуль содержит:
- Парсинг DXF файлов с извлечением геометрии
- Извлечение данных из стандартных таблиц заказчика
- Логирование ручных корректировок
- Сериализацию данных в формат для ML
- Валидацию и обработку данных
"""

from .correction_logger import CorrectionEvent, DataCollectionLogger
from .data_serializer import MLDataSerializer
from .dxf_parser import DxfParser
from .schemas import DataCollectionConfig
from .table_extractor import TableDataExtractor

__all__ = [
    "DxfParser",
    "TableDataExtractor",
    "DataCollectionLogger",
    "CorrectionEvent",
    "MLDataSerializer",
    "DataCollectionConfig",
]
