"""
Пользовательский интерфейс для системы оптимизации раскроя МДФ.

Этот модуль содержит:
- Desktop GUI приложение (PyQt6)
- Интерактивные компоненты
- Визуализацию карт раскроя
- Управление пользовательскими настройками
"""

from .components import CuttingCanvas, DetailsPanel, MaterialPanel
from .desktop_app import CuttingApp

__all__ = ["CuttingApp", "CuttingCanvas", "MaterialPanel", "DetailsPanel"]
