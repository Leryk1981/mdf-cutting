"""
MDF Cutting Optimizer

Система для оптимизации раскроя МДФ с функциями AI-коррекции карт раскроя.
Промышленное решение для автоматизации процесса учета остатков и оптимизации раскроя.

Основные компоненты:
- core: Основные алгоритмы упаковки и оптимизации
- ui: Пользовательский интерфейс (GUI)
- data: Менеджеры данных и работы с файлами
- ai_module: AI-модуль для автоматической корректировки
- utils: Вспомогательные утилиты

Пример использования:
    from mdf_cutting.core.optimizer import CuttingOptimizer
    from mdf_cutting.ui.desktop_app import CuttingApp

    optimizer = CuttingOptimizer()
    app = CuttingApp()
    app.run()
"""

__version__ = "0.1.0"
__author__ = "AI Development Team"
__email__ = "dev@mdf-cutting.com"

# Основные импорты
from .core.optimizer import CuttingOptimizer
from .data.managers import DataManager
from .ui.desktop_app import CuttingApp

__all__ = [
    "CuttingOptimizer",
    "CuttingApp",
    "DataManager",
    "__version__",
    "__author__",
    "__email__",
]
