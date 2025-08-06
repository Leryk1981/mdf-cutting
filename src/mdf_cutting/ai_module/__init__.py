"""
AI модуль для автоматической корректировки карт раскроя.

Этот модуль содержит:
- Парсинг и анализ DXF файлов
- ML-модели для предсказания корректировок
- Системы валидации изменений
- Интеграцию с основной системой раскроя
"""

# Основные компоненты
from .core.models import (
    CorrectionPredictionModel,
    EnsembleCorrectionModel,
    CorrectionReinforcementModel,
    HybridCorrectionModel,
    CuttingMapCNN,
    AttentionCorrectionModel,
    TransformerCorrectionModel
)

from .core.trainers import (
    CorrectionModelTrainer,
    ReinforcementTrainer,
    EnsembleTrainer,
    ModelEvaluator
)

# Система признаков
from .features.geometry import GeometryFeatureExtractor
from .features.optimization import OptimizationFeatureExtractor
from .features.material import MaterialFeatureExtractor

# Утилиты
from .utils.data_loader import MLDataLoader, CuttingMapDataset, DataPreprocessor
from .utils.metrics import CorrectionMetrics
from .utils.visualization import CorrectionVisualizer

# API для интеграции
from .api.correction_api import CorrectionAPI

# Устаревшие импорты (для обратной совместимости)
from .data_collector import DataCollector
from .dxf_parser import DXFParser
from .ml_model import CuttingOptimizer
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
    "DataCollector"
]
