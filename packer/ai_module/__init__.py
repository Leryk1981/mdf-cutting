"""
AI модуль для автоматической корректировки карт раскроя

Этот модуль содержит компоненты для:
- Парсинга и анализа DXF файлов
- ML-модели для предсказания корректировок
- Системы валидации изменений
- Интеграции с основной системой раскроя
"""

from .dxf_parser import DXFParser
from .ml_model import CuttingOptimizer
from .validator import LayoutValidator
from .data_collector import DataCollector

__version__ = "1.0.0"
__author__ = "AI Development Team"

__all__ = [
    'DXFParser',
    'CuttingOptimizer', 
    'LayoutValidator',
    'DataCollector'
] 