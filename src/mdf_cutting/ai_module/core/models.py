"""
ML-модели для оптимизации раскроя.

Этот модуль содержит:
- Архитектуру нейронных сетей
- Модели предсказания корректировок
- Ансамблевые и гибридные модели
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class CorrectionPredictionModel(nn.Module):
    """Модель для предсказания корректировок карт раскроя"""
    
    def __init__(self, feature_dims: Dict[str, int], hidden_dims: List[int] = [512, 256, 128]):
        super().__init__()
        
        # Сводная информация о размерностях признаков
        self.global_dim = feature_dims.get("global", 64)
        self.local_dim = feature_dims.get("local", 128)
        self.spatial_dim = feature_dims.get("spatial", 64)
        self.topo_dim = feature_dims.get("topological", 32)
        self.optim_dim = feature_dims.get("optimization", 32)
        
        # Энкодеры для разных типов признаков
        self.global_encoder = nn.Sequential(
            nn.Linear(self.global_dim, hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dims[0], hidden_dims[1] // 2),
            nn.ReLU()
        )
        
        self.local_encoder = nn.Sequential(
            nn.Linear(self.local_dim, hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dims[0], hidden_dims[1] // 2),
            nn.ReLU()
        )
        
        self.spatial_topo_encoder = nn.Sequential(
            nn.Linear(self.spatial_dim + self.topo_dim, hidden_dims[0] // 2),
            nn.ReLU(),
            nn.Linear(hidden_dims[0] // 2, hidden_dims[1] // 2),
            nn.ReLU()
        )
        
        self.optim_encoder = nn.Sequential(
            nn.Linear(self.optim_dim, hidden_dims[1] // 4),
            nn.ReLU(),
            nn.Linear(hidden_dims[1] // 4, hidden_dims[1] // 4),
            nn.ReLU()
        )
        
        # Сводный энкодер
        self.fusion_encoder = nn.Sequential(
            nn.Linear(hidden_dims[1] // 2 * 3 + hidden_dims[1] // 4, hidden_dims[1]),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dims[1], hidden_dims[2]),
            nn.ReLU()
        )
        
        # Голова для предсказания типа корректировки
        self.correction_type_head = nn.Sequential(
            nn.Linear(hidden_dims[2], hidden_dims[2] // 2),
            nn.ReLU(),
            nn.Linear(hidden_dims[2] // 2, 4)  # 4 типа корректировок
        )
        
        # Голова для предсказания параметров корректировки
        self.correction_params_head = nn.Sequential(
            nn.Linear(hidden_dims[2], hidden_dims[2] // 2),
            nn.ReLU(),
            nn.Linear(hidden_dims[2] // 2, 5)  # dx, dy, rotation, scale_x, scale_y
        )
        
        # Голова для предсказания улучшения
        self.improvement_head = nn.Sequential(
            nn.Linear(hidden_dims[2], hidden_dims[2] // 2),
            nn.ReLU(),
            nn.Linear(hidden_dims[2] // 2, 1),
            nn.Sigmoid()  # Оценка улучшения от 0 до 1
        )
    
    def forward(self, features: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        # Обработка каждого типа признаков
        global_features = self.global_encoder(features["global"])
        local_features = self.local_encoder(features["local"])
        
        spatial_topo = torch.cat([features["spatial"], features["topological"]], dim=1)
        spatial_topo_features = self.spatial_topo_encoder(spatial_topo)
        
        optim_features = self.optim_encoder(features["optimization"])
        
        # Объединение всех признаков
        combined = torch.cat([
            global_features,
            local_features,
            spatial_topo_features,
            optim_features
        ], dim=1)
        
        # Сводное представление
        fused = self.fusion_encoder(combined)
        
        # Предсказания
        output = {
            "correction_type": self.correction_type_head(fused),
            "correction_params": self.correction_params_head(fused),
            "improvement_score": self.improvement_head(fused)
        }
        
        return output


class CuttingMapCNN(nn.Module):
    """CNN для обработки визуального представления карты раскроя"""
    
    def __init__(self, input_channels: int = 3, feature_dim: int = 128):
        super().__init__()
        
        # CNN энкодер
        self.encoder = nn.Sequential(
            nn.Conv2d(input_channels, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        
        # Классификатор эффективности
        self.efficiency_head = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
        # Детектор проблемных областей
        self.problem_detector = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 4)  # 4 типа проблем
        )
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        features = self.encoder(x)
        features_flat = features.view(features.size(0), -1)
        
        return {
            "efficiency_score": self.efficiency_head(features_flat),
            "problem_types": self.problem_detector(features_flat)
        }


class EnsembleCorrectionModel(nn.Module):
    """Ансамбль моделей для предсказания корректировок"""
    
    def __init__(self, feature_dims: Dict[str, int], num_models: int = 3):
        super().__init__()
        
        self.num_models = num_models
        
        # Создаем несколько моделей с разными архитектурами
        self.models = nn.ModuleList([
            CorrectionPredictionModel(feature_dims, [512, 256, 128]),
            CorrectionPredictionModel(feature_dims, [256, 128, 64]),
            CorrectionPredictionModel(feature_dims, [1024, 512, 256])
        ])
        
        # Мета-обучатель для объединения предсказаний
        self.meta_learner = nn.Sequential(
            nn.Linear(num_models * 10, 64),  # 10 = 4 (type) + 5 (params) + 1 (improvement)
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 10)
        )
        
        # Веса для взвешенного голосования
        self.ensemble_weights = nn.Parameter(torch.ones(num_models) / num_models)
    
    def forward(self, features: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        # Получаем предсказания от всех моделей
        predictions = []
        for model in self.models:
            pred = model(features)
            # Объединяем все выходы в один вектор
            combined = torch.cat([
                pred["correction_type"],
                pred["correction_params"],
                pred["improvement_score"]
            ], dim=1)
            predictions.append(combined)
        
        # Объединяем предсказания
        ensemble_input = torch.cat(predictions, dim=1)
        
        # Мета-обучатель
        meta_output = self.meta_learner(ensemble_input)
        
        # Разделяем выход мета-обучателя
        correction_type = meta_output[:, :4]
        correction_params = meta_output[:, 4:9]
        improvement_score = torch.sigmoid(meta_output[:, 9:])
        
        return {
            "correction_type": correction_type,
            "correction_params": correction_params,
            "improvement_score": improvement_score,
            "ensemble_predictions": predictions,
            "ensemble_weights": F.softmax(self.ensemble_weights, dim=0)
        }


class CorrectionReinforcementModel(nn.Module):
    """Модель с обучением с подкреплением для оптимизации корректировок"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = [256, 128]):
        super().__init__()
        
        # Сеть ценности состояний (критик)
        self.critic = nn.Sequential(
            nn.Linear(state_dim, hidden_dims[0]),
            nn.ReLU(),
            nn.Linear(hidden_dims[0], hidden_dims[1]),
            nn.ReLU(),
            nn.Linear(hidden_dims[1], 1)
        )
        
        # Сеть политики (актор)
        self.actor = nn.Sequential(
            nn.Linear(state_dim, hidden_dims[0]),
            nn.ReLU(),
            nn.Linear(hidden_dims[0], hidden_dims[1]),
            nn.ReLU(),
            nn.Linear(hidden_dims[1], action_dim),
            nn.Softmax(dim=-1)
        )
    
    def forward(self, state):
        state_value = self.critic(state)
        action_probs = self.actor(state)
        return state_value, action_probs
    
    def get_action(self, state):
        _, action_probs = self.forward(state)
        dist = torch.distributions.Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        return action.item(), log_prob


class HybridCorrectionModel(nn.Module):
    """Гибридная модель, объединяющая предсказания и RL"""
    
    def __init__(self, prediction_model: CorrectionPredictionModel, 
                 rl_model: CorrectionReinforcementModel,
                 fusion_dim: int = 256):
        super().__init__()
        
        self.prediction_model = prediction_model
        self.rl_model = rl_model
        
        # Сеть для объединения предсказаний
        combined_input_dim = (
            prediction_model.correction_params_head[-1].out_features + 
            rl_model.critic[-1].out_features
        )
        
        self.fusion_network = nn.Sequential(
            nn.Linear(combined_input_dim, fusion_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(fusion_dim, fusion_dim // 2),
            nn.ReLU(),
            nn.Linear(fusion_dim // 2, 5)  # финальные параметры коррекции
        )
        
        self.confidence_head = nn.Sequential(
            nn.Linear(fusion_dim // 2, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    
    def forward(self, features: Dict[str, torch.Tensor], 
                rl_state: torch.Tensor = None):
        # Получаем предсказания от модели предсказаний
        prediction_output = self.prediction_model(features)
        
        # Если есть состояние для RL, используем его
        if rl_state is not None:
            rl_value, rl_action = self.rl_model(rl_state)
            rl_features = torch.cat([rl_value, rl_action], dim=-1)
        else:
            batch_size = next(iter(features.values())).size(0)
            rl_features = torch.zeros(batch_size, 2).to(next(iter(features.values())).device)
        
        # Объединяем признаки
        combined = torch.cat([
            prediction_output["correction_params"],
            rl_features
        ], dim=-1)
        
        # Финальные предсказания
        final_params = self.fusion_network(combined)
        confidence = self.confidence_head(combined[:, :final_params.size(1)//2])
        
        return {
            "correction_params": final_params,
            "confidence": confidence,
            "prediction_output": prediction_output,
            "rl_output": rl_features
        }


class AttentionCorrectionModel(nn.Module):
    """Модель с механизмом внимания для анализа карт раскроя"""
    
    def __init__(self, feature_dim: int, num_heads: int = 8, num_layers: int = 3):
        super().__init__()
        
        self.feature_dim = feature_dim
        self.num_heads = num_heads
        
        # Multi-head attention
        self.attention_layers = nn.ModuleList([
            nn.MultiheadAttention(feature_dim, num_heads, batch_first=True)
            for _ in range(num_layers)
        ])
        
        # Feed-forward сети
        self.ff_layers = nn.ModuleList([
            nn.Sequential(
                nn.Linear(feature_dim, feature_dim * 4),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(feature_dim * 4, feature_dim)
            )
            for _ in range(num_layers)
        ])
        
        # Layer normalization
        self.norm_layers = nn.ModuleList([
            nn.LayerNorm(feature_dim)
            for _ in range(num_layers * 2)
        ])
        
        # Выходные головы
        self.correction_head = nn.Sequential(
            nn.Linear(feature_dim, feature_dim // 2),
            nn.ReLU(),
            nn.Linear(feature_dim // 2, 5)
        )
        
        self.importance_head = nn.Sequential(
            nn.Linear(feature_dim, feature_dim // 2),
            nn.ReLU(),
            nn.Linear(feature_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(self, features: torch.Tensor, mask: torch.Tensor = None) -> Dict[str, torch.Tensor]:
        # features: [batch_size, seq_len, feature_dim]
        x = features
        
        # Проходим через слои attention
        for i in range(len(self.attention_layers)):
            # Self-attention
            attn_out, attn_weights = self.attention_layers[i](
                x, x, x, attn_mask=mask
            )
            x = self.norm_layers[i * 2](x + attn_out)
            
            # Feed-forward
            ff_out = self.ff_layers[i](x)
            x = self.norm_layers[i * 2 + 1](x + ff_out)
        
        # Глобальное среднее для получения представления
        global_repr = torch.mean(x, dim=1)
        
        # Предсказания
        correction_params = self.correction_head(global_repr)
        importance_score = self.importance_head(global_repr)
        
        return {
            "correction_params": correction_params,
            "importance_score": importance_score,
            "attention_weights": attn_weights if 'attn_weights' in locals() else None,
            "sequence_features": x
        }


class TransformerCorrectionModel(nn.Module):
    """Трансформер для анализа последовательностей деталей"""
    
    def __init__(self, feature_dim: int, num_heads: int = 8, num_layers: int = 6, 
                 d_model: int = 512, d_ff: int = 2048, dropout: float = 0.1):
        super().__init__()
        
        self.feature_dim = feature_dim
        self.d_model = d_model
        
        # Проекция входных признаков
        self.input_projection = nn.Linear(feature_dim, d_model)
        
        # Позиционное кодирование
        self.pos_encoding = nn.Parameter(torch.randn(1000, d_model))
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=num_heads,
            dim_feedforward=d_ff,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        
        # Выходные головы
        self.correction_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 5)
        )
        
        self.quality_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(self, features: torch.Tensor, mask: torch.Tensor = None) -> Dict[str, torch.Tensor]:
        # features: [batch_size, seq_len, feature_dim]
        batch_size, seq_len, _ = features.shape
        
        # Проекция в d_model
        x = self.input_projection(features)
        
        # Добавление позиционного кодирования
        pos_enc = self.pos_encoding[:seq_len].unsqueeze(0).expand(batch_size, -1, -1)
        x = x + pos_enc
        
        # Transformer encoding
        if mask is not None:
            x = self.transformer(x, src_key_padding_mask=mask)
        else:
            x = self.transformer(x)
        
        # Глобальное представление (CLS token или среднее)
        global_repr = torch.mean(x, dim=1)
        
        # Предсказания
        correction_params = self.correction_head(global_repr)
        quality_score = self.quality_head(global_repr)
        
        return {
            "correction_params": correction_params,
            "quality_score": quality_score,
            "sequence_features": x
        } 