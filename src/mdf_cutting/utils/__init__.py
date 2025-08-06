"""
Вспомогательные утилиты для системы оптимизации раскроя.

Этот модуль содержит:
- Логирование и отладку
- Математические вычисления
- Работу с файлами
- Общие утилиты
"""

from .logger import setup_logger
from .math_utils import calculate_area, optimize_placement
from .file_utils import safe_filename, create_backup

__all__ = [
    'setup_logger',
    'calculate_area',
    'optimize_placement',
    'safe_filename',
    'create_backup'
] 