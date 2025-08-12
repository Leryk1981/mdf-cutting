"""
Тесты для интеграционного слоя AI-модуля.

Тестирует:
- AIIntegrationService
- OptimizationBridge
- ValidationEngine
- FeedbackCollector
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

pytest.importorskip("torch")

from src.mdf_cutting.ai_module.api.correction_api import CorrectionAPI
from src.mdf_cutting.integration.ai_integration_service import (
    AIIntegrationService,
)
from src.mdf_cutting.integration.feedback_collector import FeedbackCollector
from src.mdf_cutting.integration.optimization_bridge import OptimizationBridge
from src.mdf_cutting.integration.validation_engine import ValidationEngine


class TestAIIntegrationService:
    """Тесты для AIIntegrationService."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_config_loader = Mock()
        self.mock_config_loader._configs = {
            "optimization_rules": {
                "ai_enabled": True,
                "leftovers_enabled": True,
                "feedback_enabled": True,
            }
        }

        with patch(
            "src.mdf_cutting.integration.ai_integration_service.CorrectionAPI"
        ), patch(
            "src.mdf_cutting.integration.ai_integration_service.CuttingOptimizer"
        ), patch(
            "src.mdf_cutting.integration.ai_integration_service.PackingAlgorithm"
        ), patch(
            "src.mdf_cutting.integration.ai_integration_service.setup_logger"
        ):
            self.service = AIIntegrationService(self.mock_config_loader)

    def test_service_initialization(self):
        """Тест инициализации сервиса."""
        assert self.service.ai_enabled is True
        assert self.service.leftovers_enabled is True
        assert self.service.feedback_enabled is True
        assert self.service.processing_stats["total_jobs"] == 0

    def test_process_cutting_job_basic(self):
        """Тест базовой обработки задания."""
        order_data = {
            "order_id": "test_order_001",
            "pieces": [
                {"id": "piece_1", "width": 100, "height": 100, "area": 10000},
                {"id": "piece_2", "width": 150, "height": 100, "area": 15000},
            ],
            "material_code": "MDF",
            "thickness": 16.0,
        }

        # Мокаем базовую оптимизацию
        self.service._perform_base_optimization = Mock(
            return_value={
                "status": "success",
                "utilization_rate": 0.85,
                "waste_percentage": 15.0,
                "dxf_file": "test.dxf",
            }
        )

        # Мокаем AI-улучшения
        self.service._apply_ai_enhancements = Mock(
            return_value={
                "enhancement_applied": True,
                "corrections": [
                    {
                        "piece_id": "piece_1",
                        "correction_type": "position",
                        "parameters": {"dx": 10, "dy": 5},
                        "confidence": 0.8,
                    }
                ],
                "ai_confidence": 0.8,
            }
        )

        result = self.service.process_cutting_job(order_data)

        assert result["status"] == "success"
        assert result["was_ai_assisted"] is True
        assert len(result["applied_corrections"]) > 0
        assert result["ai_confidence"] == 0.8

    def test_process_cutting_job_with_leftovers(self):
        """Тест обработки с остатками."""
        order_data = {
            "order_id": "test_order_002",
            "pieces": [
                {"id": "piece_1", "width": 100, "height": 100, "area": 10000}
            ],
            "material_code": "MDF",
            "thickness": 16.0,
        }

        # Мокаем анализ остатков
        self.service._analyze_leftovers = Mock(
            return_value={
                "use_leftovers": True,
                "suitable_leftovers": [{"id": "leftover_1", "area": 50000}],
                "estimation_savings": 25.0,
            }
        )

        # Мокаем оптимизацию с остатками
        self.service._optimize_with_leftovers = Mock(
            return_value={
                "status": "success",
                "optimization_strategy": "with_leftovers",
                "material_savings": 25.0,
            }
        )

        result = self.service.process_cutting_job(order_data)

        assert result["leftovers_analysis"]["use_leftovers"] is True
        assert result["leftovers_analysis"]["estimation_savings"] == 25.0

    def test_collect_feedback(self):
        """Тест сбора обратной связи."""
        feedback_data = {
            "job_id": "test_job_001",
            "satisfaction_rating": 4,
            "accepted_corrections": ["correction_1"],
            "rejected_corrections": [],
            "comments": "Отличная работа AI!",
        }

        result = self.service.collect_feedback(feedback_data)
        assert result != "feedback_disabled"

    def test_get_ai_effectiveness_metrics(self):
        """Тест получения метрик эффективности."""
        metrics = self.service.get_ai_effectiveness_metrics()

        assert "total_jobs" in metrics
        assert "ai_assisted_jobs" in metrics
        assert "average_processing_time" in metrics
        assert "ai_usage_rate" in metrics


class TestOptimizationBridge:
    """Тесты для OptimizationBridge."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_ai_api = Mock(spec=CorrectionAPI)
        self.bridge = OptimizationBridge(self.mock_ai_api)

    def test_bridge_initialization(self):
        """Тест инициализации моста."""
        assert self.bridge.utilization_threshold == 0.8
        assert self.bridge.waste_threshold == 20.0
        assert self.bridge.improvement_threshold == 0.05

    def test_enhance_optimization_high_quality(self):
        """Тест улучшения высококачественной оптимизации."""
        base_result = {
            "utilization_rate": 0.95,
            "waste_percentage": 5.0,
            "dxf_data": {"entities": []},
            "current_metrics": {
                "utilization_rate": 0.95,
                "waste_percentage": 5.0,
                "total_pieces": 10,
            },
        }

        order_data = {
            "pieces": [{"id": "piece_1", "area": 10000}],
            "material_code": "MDF",
        }

        result = self.bridge.enhance_optimization(base_result, order_data)

        assert result["enhancement_recommended"] is False
        assert len(result["improvement_areas"]) == 0

    def test_enhance_optimization_low_quality(self):
        """Тест улучшения низкокачественной оптимизации."""
        base_result = {
            "utilization_rate": 0.6,
            "waste_percentage": 40.0,
            "dxf_data": {"entities": []},
            "current_metrics": {
                "utilization_rate": 0.6,
                "waste_percentage": 40.0,
                "total_pieces": 10,
            },
        }

        order_data = {
            "pieces": [{"id": "piece_1", "area": 10000}],
            "material_code": "MDF",
        }

        # Мокаем AI API
        self.mock_ai_api.get_corrections.return_value = {
            "status": "success",
            "corrections": [
                {
                    "piece_id": "piece_1",
                    "correction_type": "position",
                    "parameters": {"dx": 10, "dy": 5},
                    "confidence": 0.8,
                }
            ],
            "quality_metrics": {"improvement_potential": 0.2},
        }

        result = self.bridge.enhance_optimization(base_result, order_data)

        assert result["enhancement_recommended"] is True
        assert len(result["improvement_areas"]) > 0
        assert len(result["ai_suggestions"]) > 0

    def test_identify_improvement_areas(self):
        """Тест определения областей улучшения."""
        analysis = {
            "utilization_rate": 0.7,
            "waste_percentage": 30.0,
            "potential_issues": ["overlap", "spacing"],
        }

        areas = self.bridge._identify_improvement_areas(analysis)

        assert len(areas) > 0
        assert any(area["area"] == "material_utilization" for area in areas)
        assert any(area["area"] == "waste_reduction" for area in areas)
        assert any(area["area"] == "placement_density" for area in areas)

    def test_calculate_optimization_score(self):
        """Тест расчета оценки оптимизации."""
        metrics = {"utilization_rate": 0.8, "waste_percentage": 20.0}

        score = self.bridge._calculate_optimization_score(metrics)

        assert 0 <= score <= 1
        assert score == 0.8  # (0.8 + 0.8) / 2


class TestValidationEngine:
    """Тесты для ValidationEngine."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_config_loader = Mock()
        self.mock_config_loader._configs = {
            "optimization_rules": {
                "min_spacing": 5.0,
                "max_cuts": 100,
                "material_constraints": {"max_scale_increase": 1.1},
            }
        }

        self.validator = ValidationEngine(self.mock_config_loader)

    def test_validator_initialization(self):
        """Тест инициализации валидатора."""
        assert self.validator.min_spacing == 5.0
        assert self.validator.max_cuts == 100
        assert self.validator.max_position_offset == 1000

    def test_validate_position_correction_valid(self):
        """Тест валидации корректной позиционной корректировки."""
        correction = {
            "piece_id": "piece_1",
            "correction_type": "position",
            "parameters": {"dx": 10, "dy": 5},
        }

        context = {"material_code": "MDF"}

        result = self.validator.validate_single_correction(correction, context)

        assert result["is_valid"] is True
        assert result["confidence_score"] > 0

    def test_validate_position_correction_invalid(self):
        """Тест валидации некорректной позиционной корректировки."""
        correction = {
            "piece_id": "piece_1",
            "correction_type": "position",
            "parameters": {"dx": 2500, "dy": 1500},  # Слишком большое смещение
        }

        context = {"material_code": "MDF"}

        result = self.validator.validate_single_correction(correction, context)

        assert result["is_valid"] is False
        assert "Position offset exceeds maximum allowed" in result["reason"]

    def test_validate_rotation_correction(self):
        """Тест валидации корректировки вращения."""
        correction = {
            "piece_id": "piece_1",
            "correction_type": "rotation",
            "parameters": {"rotation": 45},
        }

        context = {"material_code": "MDF"}

        result = self.validator.validate_single_correction(correction, context)

        assert result["is_valid"] is True
        assert (
            "potential_additional_cuts" in result["technological_violations"]
        )

    def test_validate_scale_correction(self):
        """Тест валидации корректировки масштабирования."""
        correction = {
            "piece_id": "piece_1",
            "correction_type": "scale",
            "parameters": {"scale_x": 1.05, "scale_y": 1.05},
        }

        context = {"material_code": "MDF"}

        result = self.validator.validate_single_correction(correction, context)

        assert result["is_valid"] is True

    def test_validate_scale_correction_invalid(self):
        """Тест валидации некорректной корректировки масштабирования."""
        correction = {
            "piece_id": "piece_1",
            "correction_type": "scale",
            "parameters": {
                "scale_x": 0.9,
                "scale_y": 0.9,
            },  # Уменьшение размера
        }

        context = {"material_code": "MDF"}

        result = self.validator.validate_single_correction(correction, context)

        assert result["is_valid"] is False
        assert "Scale must not reduce piece size" in result["reason"]

    def test_validate_suggestions_list(self):
        """Тест валидации списка предложений."""
        suggestions = [
            {
                "piece_id": "piece_1",
                "correction_type": "position",
                "parameters": {"dx": 10, "dy": 5},
            },
            {
                "piece_id": "piece_2",
                "correction_type": "position",
                "parameters": {"dx": 2500, "dy": 1500},  # Невалидная
            },
        ]

        order_data = {"material_code": "MDF"}

        validated = self.validator.validate_suggestions(
            suggestions, order_data
        )

        assert len(validated) == 1  # Только первая валидна
        assert validated[0]["piece_id"] == "piece_1"

    def test_get_validation_statistics(self):
        """Тест получения статистики валидации."""
        stats = self.validator.get_validation_statistics()

        assert "total_suggestions" in stats
        assert "rejected_suggestions" in stats
        assert "acceptance_rate" in stats
        assert "common_rejection_reasons" in stats


class TestFeedbackCollector:
    """Тесты для FeedbackCollector."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_config_loader = Mock()
        self.mock_config_loader._configs = {
            "optimization_rules": {
                "feedback_enabled": True,
                "auto_analysis_enabled": True,
            }
        }

        # Создаем временную директорию для тестов
        self.test_feedback_dir = Path("test_data/feedback")
        self.test_feedback_dir.mkdir(parents=True, exist_ok=True)

        with patch(
            "src.mdf_cutting.integration.feedback_collector.Path"
        ) as mock_path:
            mock_path.return_value = self.test_feedback_dir
            self.collector = FeedbackCollector(self.mock_config_loader)

    def teardown_method(self):
        """Очистка после каждого теста."""
        import shutil

        if self.test_feedback_dir.exists():
            shutil.rmtree(self.test_feedback_dir)

    def test_collector_initialization(self):
        """Тест инициализации коллектора."""
        assert self.collector.feedback_enabled is True
        assert self.collector.auto_analysis_enabled is True

    def test_collect_feedback_valid(self):
        """Тест сбора валидной обратной связи."""
        feedback_data = {
            "job_id": "test_job_001",
            "satisfaction_rating": 4,
            "accepted_corrections": ["correction_1"],
            "rejected_corrections": [],
            "comments": "Отличная работа!",
        }

        result = self.collector.collect_feedback(feedback_data)

        assert not result.startswith("feedback_error")
        assert not result.startswith("validation_failed")

    def test_collect_feedback_invalid_rating(self):
        """Тест сбора обратной связи с невалидным рейтингом."""
        feedback_data = {
            "job_id": "test_job_002",
            "satisfaction_rating": 6,  # Невалидный рейтинг
            "accepted_corrections": [],
            "rejected_corrections": [],
        }

        result = self.collector.collect_feedback(feedback_data)

        assert result.startswith("validation_failed")

    def test_collect_feedback_missing_fields(self):
        """Тест сбора обратной связи с отсутствующими полями."""
        feedback_data = {
            "accepted_corrections": [],
            "rejected_corrections": [],
            # Отсутствует job_id и satisfaction_rating
        }

        result = self.collector.collect_feedback(feedback_data)

        assert result.startswith("validation_failed")

    def test_get_feedback_summary(self):
        """Тест получения сводки обратной связи."""
        # Создаем тестовые данные
        test_feedback = {
            "feedback_id": "test_001",
            "timestamp": "2024-01-01T10:00:00",
            "job_id": "job_001",
            "satisfaction_rating": 4,
            "accepted_corrections": ["corr_1"],
            "rejected_corrections": [],
        }

        feedback_file = self.test_feedback_dir / "feedback_test_001.json"
        with open(feedback_file, "w") as f:
            json.dump(test_feedback, f)

        summary = self.collector.get_feedback_summary(30)

        assert "total_feedback_entries" in summary
        assert "average_satisfaction" in summary

    def test_get_ai_effectiveness_metrics(self):
        """Тест получения метрик эффективности AI."""
        metrics = self.collector.get_ai_effectiveness_metrics()

        assert "total_sessions" in metrics
        assert "average_satisfaction" in metrics
        assert "suggestion_acceptance_rate" in metrics
        assert "ai_effectiveness_score" in metrics

    def test_get_feedback_trends(self):
        """Тест получения трендов обратной связи."""
        trends = self.collector.get_feedback_trends(30)

        assert "period_days" in trends
        assert "trends" in trends
        assert "insights" in trends

    def test_validate_feedback_data(self):
        """Тест валидации данных обратной связи."""
        valid_data = {
            "job_id": "test_job",
            "satisfaction_rating": 4,
            "accepted_corrections": [],
            "rejected_corrections": [],
        }

        result = self.collector._validate_feedback_data(valid_data)

        assert result["is_valid"] is True

    def test_validate_feedback_data_invalid(self):
        """Тест валидации невалидных данных обратной связи."""
        invalid_data = {
            "job_id": "test_job",
            "satisfaction_rating": 6,  # Невалидный рейтинг
            "accepted_corrections": [],
            "rejected_corrections": [],
        }

        result = self.collector._validate_feedback_data(invalid_data)

        assert result["is_valid"] is False
        assert "Invalid satisfaction rating" in result["reason"]


class TestIntegrationWorkflow:
    """Интеграционные тесты рабочего процесса."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_config_loader = Mock()
        self.mock_config_loader._configs = {
            "optimization_rules": {
                "ai_enabled": True,
                "leftovers_enabled": True,
                "feedback_enabled": True,
            }
        }

    def test_full_integration_workflow(self):
        """Тест полного интеграционного рабочего процесса."""
        # Создаем тестовые данные
        order_data = {
            "order_id": "integration_test_001",
            "pieces": [
                {"id": "piece_1", "width": 100, "height": 100, "area": 10000},
                {"id": "piece_2", "width": 150, "height": 100, "area": 15000},
            ],
            "material_code": "MDF",
            "thickness": 16.0,
        }

        # Мокаем все компоненты
        with patch(
            "src.mdf_cutting.integration.ai_integration_service.CorrectionAPI"
        ), patch(
            "src.mdf_cutting.integration.ai_integration_service.CuttingOptimizer"
        ), patch(
            "src.mdf_cutting.integration.ai_integration_service.PackingAlgorithm"
        ), patch(
            "src.mdf_cutting.integration.ai_integration_service.setup_logger"
        ):
            service = AIIntegrationService(self.mock_config_loader)

            # Мокаем методы
            service._perform_base_optimization = Mock(
                return_value={
                    "status": "success",
                    "utilization_rate": 0.7,
                    "waste_percentage": 30.0,
                    "dxf_file": "test.dxf",
                }
            )

            service._apply_ai_enhancements = Mock(
                return_value={
                    "enhancement_applied": True,
                    "corrections": [
                        {
                            "piece_id": "piece_1",
                            "correction_type": "position",
                            "parameters": {"dx": 10, "dy": 5},
                            "confidence": 0.8,
                        }
                    ],
                    "ai_confidence": 0.8,
                }
            )

            # Выполняем обработку
            result = service.process_cutting_job(order_data)

            # Проверяем результат
            assert result["status"] == "success"
            assert result["was_ai_assisted"] is True
            assert len(result["applied_corrections"]) > 0

            # Собираем обратную связь
            feedback_data = {
                "job_id": order_data["order_id"],
                "satisfaction_rating": 4,
                "accepted_corrections": ["piece_1"],
                "rejected_corrections": [],
                "comments": "Отличная интеграция!",
            }

            feedback_result = service.collect_feedback(feedback_data)
            assert feedback_result != "feedback_disabled"

            # Получаем метрики
            metrics = service.get_ai_effectiveness_metrics()
            assert "total_jobs" in metrics
            assert "ai_assisted_jobs" in metrics
