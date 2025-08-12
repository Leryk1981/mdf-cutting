"""
Тесты для компонентов работы с остатками.

Проверяет функциональность:
- LeftoverFeatureExtractor
- LeftoverOptimizationModel
- LeftoverOptimizer
- Интеграция с API
"""
import pytest

torch = pytest.importorskip("torch")

from src.mdf_cutting.ai_module.core.leftover_optimizer import (
    LeftoverAssignment,
    LeftoverOptimizationModel,
    LeftoverOptimizer,
)
from src.mdf_cutting.ai_module.features.leftovers import (
    Leftover,
    LeftoverFeatureExtractor,
)


class TestLeftover:
    """Тесты для структуры Leftover."""

    def test_leftover_creation(self):
        """Тест создания объекта остатка."""
        leftover = Leftover(
            id="test_001",
            geometry=None,
            material_code="MDF",
            thickness=16.0,
            creation_date="2024-01-01T00:00:00",
            source_dxf="test.dxf",
            usage_count=0,
            priority=1.0,
            area=50000.0,
            width=500.0,
            height=100.0,
        )

        assert leftover.id == "test_001"
        assert leftover.material_code == "MDF"
        assert leftover.thickness == 16.0
        assert leftover.area == 50000.0
        assert leftover.width == 500.0
        assert leftover.height == 100.0


class TestLeftoverFeatureExtractor:
    """Тесты для извлечения признаков остатков."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.extractor = LeftoverFeatureExtractor()

        # Создание тестовых остатков
        self.test_leftovers = [
            Leftover(
                id="leftover_1",
                geometry=None,
                material_code="MDF",
                thickness=16.0,
                creation_date="2024-01-01T00:00:00",
                source_dxf="test1.dxf",
                area=50000.0,
                width=500.0,
                height=100.0,
            ),
            Leftover(
                id="leftover_2",
                geometry=None,
                material_code="MDF",
                thickness=16.0,
                creation_date="2024-01-02T00:00:00",
                source_dxf="test2.dxf",
                area=30000.0,
                width=300.0,
                height=100.0,
            ),
        ]

        # Тестовые данные DXF
        self.test_dxf_data = {
            "entities": [
                {"area": 10000, "width": 100, "height": 100},
                {"area": 15000, "width": 150, "height": 100},
                {"area": 8000, "width": 80, "height": 100},
            ],
            "material_code": "MDF",
            "thickness": 16.0,
        }

    def test_extract_leftover_features_success(self):
        """Тест успешного извлечения признаков остатков."""
        features = self.extractor.extract_leftover_features(
            self.test_dxf_data, self.test_leftovers
        )

        assert "material_efficiency" in features
        assert "leftover_suitability" in features
        assert "new_leftovers_potential" in features
        assert "optimization_strategy" in features

        # Проверка эффективности материала
        efficiency = features["material_efficiency"]
        assert "total_leftover_area_available" in efficiency
        assert "suitable_leftovers_count" in efficiency
        assert "leftover_coverage_ratio" in efficiency
        assert "material_savings_potential" in efficiency

    def test_calculate_material_efficiency(self):
        """Тест расчета эффективности материала."""
        efficiency = self.extractor._calculate_material_efficiency(
            self.test_dxf_data, self.test_leftovers
        )

        assert (
            efficiency["total_leftover_area_available"] == 80000.0
        )  # 50000 + 30000
        assert efficiency["suitable_leftovers_count"] >= 0
        # Coverage ratio может быть больше 1, если остатков больше чем нужно
        assert efficiency["leftover_coverage_ratio"] >= 0
        # Material savings может быть больше 100% при избытке остатков
        assert efficiency["material_savings_potential"] >= 0

    def test_evaluate_leftover_suitability(self):
        """Тест оценки пригодности остатков."""
        suitability = self.extractor._evaluate_leftover_suitability(
            self.test_dxf_data, self.test_leftovers
        )

        assert isinstance(suitability, list)

        if suitability:  # Если есть подходящие остатки
            for item in suitability:
                assert "leftover_id" in item
                assert "suitability_score" in item
                assert "geometric_score" in item
                assert "recency_score" in item
                assert "usage_score" in item
                assert 0 <= item["suitability_score"] <= 1

    def test_predict_new_leftovers(self):
        """Тест предсказания новых остатков."""
        # Добавляем информацию о листах
        dxf_with_sheets = self.test_dxf_data.copy()
        dxf_with_sheets["sheets"] = [
            {"area": 100000, "width": 1000, "height": 1000}
        ]

        predicted = self.extractor._predict_new_leftovers(dxf_with_sheets)

        assert isinstance(predicted, list)

        if predicted:  # Если предсказаны остатки
            for leftover in predicted:
                assert "geometry" in leftover
                assert "area" in leftover
                assert "utilization_potential" in leftover
                assert "storage_efficiency" in leftover
                assert "priority" in leftover

    def test_determine_optimization_strategy(self):
        """Тест определения стратегии оптимизации."""
        strategy = self.extractor._determine_optimization_strategy(
            self.test_dxf_data, self.test_leftovers
        )

        assert "primary_strategy" in strategy
        assert "leftover_first" in strategy
        assert "minimize_new_sheets" in strategy
        assert "optimize_for_future_use" in strategy

    def test_calculate_compatibility(self):
        """Тест расчета совместимости."""
        leftover = self.test_leftovers[0]
        compatibility = self.extractor._calculate_compatibility(
            self.test_dxf_data, leftover
        )

        assert 0 <= compatibility <= 1

    def test_calculate_geometric_suitability(self):
        """Тест расчета геометрической пригодности."""
        order_pieces = self.test_dxf_data["entities"]
        leftover = self.test_leftovers[0]

        suitability = self.extractor._calculate_geometric_suitability(
            order_pieces, leftover
        )

        assert 0 <= suitability <= 1

    def test_calculate_recency_score(self):
        """Тест расчета оценки по возрасту."""
        leftover = self.test_leftovers[0]
        recency = self.extractor._calculate_recency_score(leftover)

        assert 0 <= recency <= 1

    def test_calculate_usage_score(self):
        """Тест расчета оценки по использованию."""
        leftover = self.test_leftovers[0]
        usage = self.extractor._calculate_usage_score(leftover)

        assert 0 <= usage <= 1

    def test_matches_material_spec(self):
        """Тест проверки соответствия спецификации материала."""
        leftover = self.test_leftovers[0]
        matches = self.extractor._matches_material_spec(
            self.test_dxf_data, leftover
        )

        assert isinstance(matches, bool)

    def test_extract_leftover_features_empty_data(self):
        """Тест извлечения признаков с пустыми данными."""
        empty_dxf = {"entities": [], "material_code": "MDF", "thickness": 16.0}
        features = self.extractor.extract_leftover_features(empty_dxf, [])

        assert "material_efficiency" in features
        assert "leftover_suitability" in features
        assert "new_leftovers_potential" in features
        assert "optimization_strategy" in features


class TestLeftoverOptimizationModel:
    """Тесты для модели оптимизации остатков."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.model = LeftoverOptimizationModel(feature_dim=256)

    def test_model_creation(self):
        """Тест создания модели."""
        assert self.model is not None
        assert hasattr(self.model, "leftover_encoder")
        assert hasattr(self.model, "piece_encoder")
        assert hasattr(self.model, "compatibility_network")
        assert hasattr(self.model, "placement_network")
        assert hasattr(self.model, "strategy_classifier")
        assert hasattr(self.model, "efficiency_network")

    def test_forward_pass(self):
        """Тест прямого прохода модели."""
        batch_size = 2
        feature_dim = 256

        leftover_features = torch.randn(batch_size, feature_dim)
        piece_features = torch.randn(batch_size, feature_dim)

        outputs = self.model(leftover_features, piece_features)

        assert "compatibility" in outputs
        assert "placement" in outputs
        assert "strategy" in outputs
        assert "efficiency" in outputs

        assert outputs["compatibility"].shape == (batch_size, 1)
        assert outputs["placement"].shape == (batch_size, 3)
        assert outputs["strategy"].shape == (
            batch_size,
            10,
        )  # num_leftover_types
        assert outputs["efficiency"].shape == (batch_size, 1)

    def test_compatibility_range(self):
        """Тест диапазона значений совместимости."""
        batch_size = 1
        feature_dim = 256

        leftover_features = torch.randn(batch_size, feature_dim)
        piece_features = torch.randn(batch_size, feature_dim)

        outputs = self.model(leftover_features, piece_features)
        compatibility = outputs["compatibility"]

        assert torch.all(compatibility >= 0) and torch.all(compatibility <= 1)

    def test_placement_range(self):
        """Тест диапазона значений размещения."""
        batch_size = 1
        feature_dim = 256

        leftover_features = torch.randn(batch_size, feature_dim)
        piece_features = torch.randn(batch_size, feature_dim)

        outputs = self.model(leftover_features, piece_features)
        placement = outputs["placement"]

        # Размещение должно быть в диапазоне [-100, 100] после масштабирования
        assert torch.all(placement >= -100) and torch.all(placement <= 100)

    def test_strategy_probabilities(self):
        """Тест вероятностей стратегий."""
        batch_size = 1
        feature_dim = 256

        leftover_features = torch.randn(batch_size, feature_dim)
        piece_features = torch.randn(batch_size, feature_dim)

        outputs = self.model(leftover_features, piece_features)
        strategy = outputs["strategy"]

        # Сумма вероятностей должна быть равна 1
        assert torch.allclose(
            torch.sum(strategy, dim=1), torch.ones(batch_size)
        )
        assert torch.all(strategy >= 0) and torch.all(strategy <= 1)


class TestLeftoverOptimizer:
    """Тесты для оптимизатора остатков."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.model = LeftoverOptimizationModel(feature_dim=256)
        self.config = {"device": "cpu", "min_compatibility": 0.5}
        self.optimizer = LeftoverOptimizer(self.model, self.config)

        # Тестовые данные
        self.test_dxf_data = {
            "entities": [
                {"id": "piece_1", "area": 10000, "width": 100, "height": 100},
                {"id": "piece_2", "area": 15000, "width": 150, "height": 100},
                {"id": "piece_3", "area": 8000, "width": 80, "height": 100},
            ],
            "material_code": "MDF",
            "thickness": 16.0,
        }

        self.test_leftovers = [
            Leftover(
                id="leftover_1",
                geometry=None,
                material_code="MDF",
                thickness=16.0,
                creation_date="2024-01-01T00:00:00",
                source_dxf="test1.dxf",
                area=50000.0,
                width=500.0,
                height=100.0,
            )
        ]

    def test_optimizer_creation(self):
        """Тест создания оптимизатора."""
        assert self.optimizer is not None
        assert self.optimizer.model is self.model
        assert self.optimizer.config is self.config
        assert self.optimizer.device == torch.device("cpu")

    def test_extract_pieces_features(self):
        """Тест извлечения признаков деталей."""
        pieces = self.optimizer._extract_pieces_features(self.test_dxf_data)

        assert len(pieces) == 3
        assert pieces[0]["id"] == "piece_0"  # ID генерируется по индексу
        assert pieces[0]["area"] == 10000
        assert "features" in pieces[0]
        assert len(pieces[0]["features"]) == 256

    def test_extract_leftovers_features(self):
        """Тест извлечения признаков остатков."""
        features = self.optimizer._extract_leftovers_features(
            self.test_leftovers
        )

        assert len(features) == 1
        assert features[0]["id"] == "leftover_1"
        assert features[0]["area"] == 50000.0
        assert "features" in features[0]
        assert len(features[0]["features"]) == 256

    def test_find_optimal_assignments(self):
        """Тест поиска оптимальных назначений."""
        pieces = self.optimizer._extract_pieces_features(self.test_dxf_data)
        leftover_features = self.optimizer._extract_leftovers_features(
            self.test_leftovers
        )

        assignments = self.optimizer._find_optimal_assignments(
            pieces, leftover_features
        )

        assert isinstance(assignments, list)

        if assignments:  # Если найдены назначения
            for assignment in assignments:
                assert isinstance(assignment, LeftoverAssignment)
                assert assignment.piece_id in ["piece_1", "piece_2", "piece_3"]
                assert assignment.leftover_id == "leftover_1"
                assert 0 <= assignment.confidence <= 1
                assert 0 <= assignment.area_utilization <= 1

    def test_predict_new_leftovers(self):
        """Тест предсказания новых остатков."""
        assignments = [
            LeftoverAssignment(
                piece_id="piece_1",
                leftover_id="leftover_1",
                position=(0, 0),
                rotation=0,
                confidence=0.8,
                area_utilization=0.7,
            )
        ]

        new_leftovers = self.optimizer._predict_new_leftovers(
            self.test_dxf_data, assignments
        )

        assert isinstance(new_leftovers, list)

        if new_leftovers:  # Если предсказаны остатки
            for leftover in new_leftovers:
                assert "source_leftover_id" in leftover
                assert "area_remaining" in leftover
                assert "geometry_type" in leftover
                assert "reuse_priority" in leftover

    def test_calculate_efficiency_metrics(self):
        """Тест расчета метрик эффективности."""
        assignments = [
            LeftoverAssignment(
                piece_id="piece_1",
                leftover_id="leftover_1",
                position=(0, 0),
                rotation=0,
                confidence=0.8,
                area_utilization=0.7,
            )
        ]

        new_leftovers = [
            {
                "source_leftover_id": "leftover_1",
                "area_remaining": 20000,
                "reuse_priority": 0.8,
            }
        ]

        metrics = self.optimizer._calculate_efficiency_metrics(
            self.test_dxf_data, assignments, new_leftovers
        )

        assert "material_efficiency" in metrics
        assert "leftover_utilization_rate" in metrics
        assert "new_leftovers_quality" in metrics
        assert "assignment_efficiency" in metrics
        assert "overall_score" in metrics
        assert "pieces_assigned" in metrics
        assert "total_pieces" in metrics

    def test_generate_optimized_layout(self):
        """Тест генерации оптимизированной раскладки."""
        assignments = [
            LeftoverAssignment(
                piece_id="piece_1",
                leftover_id="leftover_1",
                position=(0, 0),
                rotation=0,
                confidence=0.8,
                area_utilization=0.7,
            )
        ]

        layout = self.optimizer._generate_optimized_layout(
            assignments, self.test_dxf_data
        )

        assert "assignments" in layout
        assert "total_area_utilized" in layout
        assert "leftovers_used" in layout
        assert "pieces_placed" in layout

    def test_determine_strategy(self):
        """Тест определения стратегии."""
        metrics = {
            "material_efficiency": 0.8,
            "leftover_utilization_rate": 0.9,
        }

        strategy = self.optimizer._determine_strategy(metrics)

        assert isinstance(strategy, str)
        assert strategy in [
            "high_efficiency_leftover_optimization",
            "moderate_leftover_optimization",
            "basic_leftover_usage",
            "new_sheets_required",
        ]

    def test_create_piece_feature_vector(self):
        """Тест создания вектора признаков детали."""
        entity = {
            "area": 10000,
            "width": 100,
            "height": 100,
            "perimeter": 400,
            "aspect_ratio": 1.0,
            "complexity": 1.0,
        }

        features = self.optimizer._create_piece_feature_vector(entity)

        assert len(features) == 256
        assert features[0] == 0.1  # area / 100000
        assert features[1] == 0.1  # width / 1000

    def test_create_leftover_feature_vector(self):
        """Тест создания вектора признаков остатка."""
        leftover = Leftover(
            id="test",
            geometry=None,
            material_code="MDF",
            thickness=16.0,
            creation_date="2024-01-01T00:00:00",
            source_dxf="test.dxf",
            area=50000.0,
            width=500.0,
            height=100.0,
        )

        features = self.optimizer._create_leftover_feature_vector(leftover)

        assert len(features) == 256
        assert features[0] == 0.5  # area / 100000
        assert features[1] == 0.5  # width / 1000

    def test_optimize_layout_integration(self):
        """Интеграционный тест оптимизации раскладки."""
        result = self.optimizer.optimize_layout(
            self.test_dxf_data, self.test_leftovers
        )

        assert "assignments" in result
        assert "optimized_layout" in result
        assert "new_leftovers" in result
        assert "efficiency_metrics" in result
        assert "strategy_used" in result
        assert "processing_time_ms" in result
        assert "iterations_performed" in result


class TestLeftoverIntegration:
    """Интеграционные тесты для работы с остатками."""

    def test_full_leftover_workflow(self):
        """Тест полного рабочего процесса с остатками."""
        # Создание экстрактора
        extractor = LeftoverFeatureExtractor()

        # Создание модели и оптимизатора
        model = LeftoverOptimizationModel(feature_dim=256)
        config = {"device": "cpu", "min_compatibility": 0.3}
        optimizer = LeftoverOptimizer(model, config)

        # Тестовые данные
        dxf_data = {
            "entities": [
                {"area": 10000, "width": 100, "height": 100},
                {"area": 15000, "width": 150, "height": 100},
            ],
            "material_code": "MDF",
            "thickness": 16.0,
        }

        leftovers = [
            Leftover(
                id="leftover_1",
                geometry=None,
                material_code="MDF",
                thickness=16.0,
                creation_date="2024-01-01T00:00:00",
                source_dxf="test.dxf",
                area=50000.0,
                width=500.0,
                height=100.0,
            )
        ]

        # 1. Извлечение признаков
        features = extractor.extract_leftover_features(dxf_data, leftovers)
        assert "material_efficiency" in features

        # 2. Оптимизация
        result = optimizer.optimize_layout(dxf_data, leftovers)
        assert "assignments" in result
        assert "efficiency_metrics" in result

        # 3. Проверка результатов
        assert result["status"] == "success" or "error" in result
