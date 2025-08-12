"""
Тесты для ML-моделей AI-модуля.
"""
import pytest

torch = pytest.importorskip("torch")

from src.mdf_cutting.ai_module.core.models import (
    CorrectionPredictionModel,
    CorrectionReinforcementModel,
    CuttingMapCNN,
    EnsembleCorrectionModel,
    HybridCorrectionModel,
)


class TestCorrectionPredictionModel:
    """Тесты для модели предсказания корректировок."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.feature_dims = {
            "global": 64,
            "local": 128,
            "spatial": 64,
            "topological": 32,
            "optimization": 32,
        }
        self.model = CorrectionPredictionModel(self.feature_dims)

    def test_model_initialization(self):
        """Тест инициализации модели."""
        assert self.model.global_dim == 64
        assert self.model.local_dim == 128
        assert self.model.spatial_dim == 64
        assert self.model.topo_dim == 32
        assert self.model.optim_dim == 32

    def test_forward_pass(self):
        """Тест прямого прохода модели."""
        # Создаем тестовые данные
        batch_size = 2
        features = {
            "global": torch.randn(batch_size, 64),
            "local": torch.randn(batch_size, 128),
            "spatial": torch.randn(batch_size, 64),
            "topological": torch.randn(batch_size, 32),
            "optimization": torch.randn(batch_size, 32),
        }

        # Прямой проход
        outputs = self.model(features)

        # Проверяем выходы
        assert "correction_type" in outputs
        assert "correction_params" in outputs
        assert "improvement_score" in outputs

        assert outputs["correction_type"].shape == (batch_size, 4)
        assert outputs["correction_params"].shape == (batch_size, 5)
        assert outputs["improvement_score"].shape == (batch_size, 1)

    def test_forward_pass_single_sample(self):
        """Тест прямого прохода для одного образца."""
        features = {
            "global": torch.randn(1, 64),
            "local": torch.randn(1, 128),
            "spatial": torch.randn(1, 64),
            "topological": torch.randn(1, 32),
            "optimization": torch.randn(1, 32),
        }

        outputs = self.model(features)

        assert outputs["correction_type"].shape == (1, 4)
        assert outputs["correction_params"].shape == (1, 5)
        assert outputs["improvement_score"].shape == (1, 1)

    def test_improvement_score_range(self):
        """Тест диапазона значений improvement_score."""
        features = {
            "global": torch.randn(1, 64),
            "local": torch.randn(1, 128),
            "spatial": torch.randn(1, 64),
            "topological": torch.randn(1, 32),
            "optimization": torch.randn(1, 32),
        }

        outputs = self.model(features)
        improvement_score = outputs["improvement_score"]

        # Проверяем, что значения в диапазоне [0, 1]
        assert torch.all(improvement_score >= 0)
        assert torch.all(improvement_score <= 1)


class TestEnsembleCorrectionModel:
    """Тесты для ансамблевой модели."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.feature_dims = {
            "global": 64,
            "local": 128,
            "spatial": 64,
            "topological": 32,
            "optimization": 32,
        }
        self.model = EnsembleCorrectionModel(self.feature_dims, num_models=3)

    def test_model_initialization(self):
        """Тест инициализации ансамблевой модели."""
        assert len(self.model.models) == 3
        assert self.model.num_models == 3

    def test_forward_pass(self):
        """Тест прямого прохода ансамблевой модели."""
        batch_size = 2
        features = {
            "global": torch.randn(batch_size, 64),
            "local": torch.randn(batch_size, 128),
            "spatial": torch.randn(batch_size, 64),
            "topological": torch.randn(batch_size, 32),
            "optimization": torch.randn(batch_size, 32),
        }

        outputs = self.model(features)

        assert "correction_type" in outputs
        assert "correction_params" in outputs
        assert "improvement_score" in outputs
        assert "ensemble_predictions" in outputs
        assert "ensemble_weights" in outputs

        assert len(outputs["ensemble_predictions"]) == 3
        assert outputs["ensemble_weights"].shape == (3,)


class TestCorrectionReinforcementModel:
    """Тесты для RL-модели."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.state_dim = 64
        self.action_dim = 4
        self.model = CorrectionReinforcementModel(
            self.state_dim, self.action_dim
        )

    def test_model_initialization(self):
        """Тест инициализации RL-модели."""
        assert self.model.critic is not None
        assert self.model.actor is not None

    def test_forward_pass(self):
        """Тест прямого прохода RL-модели."""
        batch_size = 2
        state = torch.randn(batch_size, self.state_dim)

        state_value, action_probs = self.model(state)

        assert state_value.shape == (batch_size, 1)
        assert action_probs.shape == (batch_size, self.action_dim)

        # Проверяем, что вероятности действий суммируются в 1
        assert torch.allclose(action_probs.sum(dim=1), torch.ones(batch_size))

    def test_get_action(self):
        """Тест получения действия."""
        state = torch.randn(1, self.state_dim)

        action, log_prob = self.model.get_action(state)

        assert isinstance(action, int)
        assert 0 <= action < self.action_dim
        assert isinstance(log_prob, torch.Tensor)


class TestCuttingMapCNN:
    """Тесты для CNN модели."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.model = CuttingMapCNN(input_channels=3, feature_dim=128)

    def test_model_initialization(self):
        """Тест инициализации CNN модели."""
        assert self.model.encoder is not None
        assert self.model.efficiency_head is not None
        assert self.model.problem_detector is not None

    def test_forward_pass(self):
        """Тест прямого прохода CNN модели."""
        batch_size = 2
        channels = 3
        height = 224
        width = 224

        x = torch.randn(batch_size, channels, height, width)

        outputs = self.model(x)

        assert "efficiency_score" in outputs
        assert "problem_types" in outputs

        assert outputs["efficiency_score"].shape == (batch_size, 1)
        assert outputs["problem_types"].shape == (batch_size, 4)

        # Проверяем диапазон efficiency_score
        efficiency_score = outputs["efficiency_score"]
        assert torch.all(efficiency_score >= 0)
        assert torch.all(efficiency_score <= 1)


class TestHybridCorrectionModel:
    """Тесты для гибридной модели."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        feature_dims = {
            "global": 64,
            "local": 128,
            "spatial": 64,
            "topological": 32,
            "optimization": 32,
        }

        self.prediction_model = CorrectionPredictionModel(feature_dims)
        self.rl_model = CorrectionReinforcementModel(
            state_dim=64, action_dim=4
        )
        self.hybrid_model = HybridCorrectionModel(
            self.prediction_model, self.rl_model
        )

    def test_model_initialization(self):
        """Тест инициализации гибридной модели."""
        assert self.hybrid_model.prediction_model is not None
        assert self.hybrid_model.rl_model is not None
        assert self.hybrid_model.fusion_network is not None
        assert self.hybrid_model.confidence_head is not None

    def test_forward_pass_without_rl_state(self):
        """Тест прямого прохода без RL состояния."""
        batch_size = 2
        features = {
            "global": torch.randn(batch_size, 64),
            "local": torch.randn(batch_size, 128),
            "spatial": torch.randn(batch_size, 64),
            "topological": torch.randn(batch_size, 32),
            "optimization": torch.randn(batch_size, 32),
        }

        outputs = self.hybrid_model(features)

        assert "correction_params" in outputs
        assert "confidence" in outputs
        assert "prediction_output" in outputs
        assert "rl_output" in outputs

        assert outputs["correction_params"].shape == (batch_size, 5)
        assert outputs["confidence"].shape == (batch_size, 1)

    def test_forward_pass_with_rl_state(self):
        """Тест прямого прохода с RL состоянием."""
        batch_size = 2
        features = {
            "global": torch.randn(batch_size, 64),
            "local": torch.randn(batch_size, 128),
            "spatial": torch.randn(batch_size, 64),
            "topological": torch.randn(batch_size, 32),
            "optimization": torch.randn(batch_size, 32),
        }
        rl_state = torch.randn(batch_size, 64)

        outputs = self.hybrid_model(features, rl_state)

        assert "correction_params" in outputs
        assert "confidence" in outputs
        assert "prediction_output" in outputs
        assert "rl_output" in outputs


class TestModelIntegration:
    """Интеграционные тесты моделей."""

    def test_model_device_compatibility(self):
        """Тест совместимости с разными устройствами."""
        feature_dims = {
            "global": 64,
            "local": 128,
            "spatial": 64,
            "topological": 32,
            "optimization": 32,
        }

        model = CorrectionPredictionModel(feature_dims)

        # Тест на CPU
        features = {
            "global": torch.randn(1, 64),
            "local": torch.randn(1, 128),
            "spatial": torch.randn(1, 64),
            "topological": torch.randn(1, 32),
            "optimization": torch.randn(1, 32),
        }

        outputs_cpu = model(features)
        assert outputs_cpu["correction_type"].device.type == "cpu"

        # Тест на GPU (если доступен)
        if torch.cuda.is_available():
            model_gpu = CorrectionPredictionModel(feature_dims).cuda()
            features_gpu = {k: v.cuda() for k, v in features.items()}

            outputs_gpu = model_gpu(features_gpu)
            assert outputs_gpu["correction_type"].device.type == "cuda"

    def test_model_serialization(self):
        """Тест сериализации модели."""
        feature_dims = {
            "global": 64,
            "local": 128,
            "spatial": 64,
            "topological": 32,
            "optimization": 32,
        }

        model = CorrectionPredictionModel(feature_dims)

        # Сохранение модели
        torch.save(model.state_dict(), "test_model.pth")

        # Загрузка модели
        new_model = CorrectionPredictionModel(feature_dims)
        new_model.load_state_dict(torch.load("test_model.pth"))

        # Проверяем, что модели идентичны
        features = {
            "global": torch.randn(1, 64),
            "local": torch.randn(1, 128),
            "spatial": torch.randn(1, 64),
            "topological": torch.randn(1, 32),
            "optimization": torch.randn(1, 32),
        }

        outputs_original = model(features)
        outputs_loaded = new_model(features)

        for key in outputs_original:
            assert torch.allclose(outputs_original[key], outputs_loaded[key])

        # Очистка
        import os

        if os.path.exists("test_model.pth"):
            os.remove("test_model.pth")
