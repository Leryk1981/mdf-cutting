"""
Основные алгоритмы упаковки и оптимизации раскроя МДФ.

Этот модуль содержит:
- Алгоритмы упаковки деталей (rectpack)
- Генерацию DXF файлов
- Управление остатками материалов
- Оптимизацию раскроя
"""

from .optimizer import CuttingOptimizer
from .packing import PackingAlgorithm
from .dxf_generator import DXFGenerator
from .remnants import RemnantsManager

__all__ = [
    'CuttingOptimizer',
    'PackingAlgorithm', 
    'DXFGenerator',
    'RemnantsManager'
] 