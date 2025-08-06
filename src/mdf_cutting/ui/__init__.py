"""
Пользовательский интерфейс для системы оптимизации раскроя МДФ.

Этот модуль содержит:
- Desktop GUI приложение (PyQt6)
- Интерактивные компоненты
- Визуализацию карт раскроя
- Управление пользовательскими настройками
"""

from .desktop_app import CuttingApp
from .components import CuttingCanvas, MaterialPanel, DetailsPanel

__all__ = [
    'CuttingApp',
    'CuttingCanvas',
    'MaterialPanel', 
    'DetailsPanel'
] 