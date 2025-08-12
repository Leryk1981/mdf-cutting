"""
Инженерия признаков для AI-модуля.

Этот модуль содержит:
- Геометрические признаки
- Признаки оптимизации
- Признаки материалов
"""

from .geometry import GeometryFeatureExtractor
from .material import MaterialFeatureExtractor
from .optimization import OptimizationFeatureExtractor

__all__ = [
    "GeometryFeatureExtractor",
    "OptimizationFeatureExtractor",
    "MaterialFeatureExtractor",
]
