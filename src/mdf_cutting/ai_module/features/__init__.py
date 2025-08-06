"""
Инженерия признаков для AI-модуля.

Этот модуль содержит:
- Геометрические признаки
- Признаки оптимизации
- Признаки материалов
"""

from .geometry import GeometryFeatureExtractor
from .optimization import OptimizationFeatureExtractor
from .material import MaterialFeatureExtractor

__all__ = [
    "GeometryFeatureExtractor",
    "OptimizationFeatureExtractor", 
    "MaterialFeatureExtractor"
] 