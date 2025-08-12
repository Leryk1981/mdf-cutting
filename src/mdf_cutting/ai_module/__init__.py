"""
AI модуль для автоматической корректировки карт раскроя.

Этот модуль содержит:
- Парсинг и анализ DXF файлов
- ML-модели для предсказания корректировок
- Системы валидации изменений
- Интеграцию с основной системой раскроя
"""

# API для интеграции
from .api.correction_api import CorrectionAPI

# Основные компоненты
from .core.models import (
    AttentionCorrectionModel,
    CorrectionPredictionModel,
    CorrectionReinforcementModel,
    CuttingMapCNN,
    EnsembleCorrectionModel,
    HybridCorrectionModel,
    TransformerCorrectionModel,
)
from .core.trainers import (
    CorrectionModelTrainer,
    EnsembleTrainer,
    ModelEvaluator,
    ReinforcementTrainer,
)

# Устаревшие импорты (для обратной совместимости)
from .data_collector import DataCollector
from .dxf_parser import DXFParser

# Система признаков
from .features.geometry import GeometryFeatureExtractor
from .features.material import MaterialFeatureExtractor
from .features.optimization import OptimizationFeatureExtractor
from .ml_model import CuttingOptimizer

# Утилиты
from .utils.data_loader import (
    CuttingMapDataset,
    DataPreprocessor,
    MLDataLoader,
)
from .utils.metrics import CorrectionMetrics
from .utils.visualization import CorrectionVisualizer
from .validator import LayoutValidator

__all__ = [
    # Основные модели
    "CorrectionPredictionModel",
    "EnsembleCorrectionModel",
    "CorrectionReinforcementModel",
    "HybridCorrectionModel",
    "CuttingMapCNN",
    "AttentionCorrectionModel",
    "TransformerCorrectionModel",
    # Тренеры
    "CorrectionModelTrainer",
    "ReinforcementTrainer",
    "EnsembleTrainer",
    "ModelEvaluator",
    # Экстракторы признаков
    "GeometryFeatureExtractor",
    "OptimizationFeatureExtractor",
    "MaterialFeatureExtractor",
    # Утилиты
    "MLDataLoader",
    "CuttingMapDataset",
    "DataPreprocessor",
    "CorrectionMetrics",
    "CorrectionVisualizer",
    # API
    "CorrectionAPI",
    # Устаревшие (для обратной совместимости)
    "DXFParser",
    "CuttingOptimizer",
    "LayoutValidator",
    "DataCollector",
]
