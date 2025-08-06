"""
AI модуль для автоматической корректировки карт раскроя.

Этот модуль содержит:
- Парсинг и анализ DXF файлов
- ML-модели для предсказания корректировок
- Системы валидации изменений
- Интеграцию с основной системой раскроя
"""

from .data_collector import DataCollector
from .dxf_parser import DXFParser
from .ml_model import CuttingOptimizer
from .validator import LayoutValidator

__all__ = ["DXFParser", "CuttingOptimizer", "LayoutValidator", "DataCollector"]
