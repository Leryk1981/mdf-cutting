"""
Основные компоненты AI-модуля.

Этот модуль содержит:
- Модели машинного обучения
- Предсказания и инференс
- Обучение моделей
"""

from .models import (
    CorrectionPredictionModel,
    EnsembleCorrectionModel,
    CorrectionReinforcementModel,
    HybridCorrectionModel,
    CuttingMapCNN
)

from .trainers import (
    CorrectionModelTrainer,
    ReinforcementTrainer
)

__all__ = [
    "CorrectionPredictionModel",
    "EnsembleCorrectionModel", 
    "CorrectionReinforcementModel",
    "HybridCorrectionModel",
    "CuttingMapCNN",
    "CorrectionModelTrainer",
    "ReinforcementTrainer"
] 