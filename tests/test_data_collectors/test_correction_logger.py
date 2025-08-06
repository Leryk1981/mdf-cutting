"""
Тесты для системы логирования корректировок.
"""

import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock
from src.mdf_cutting.data_collectors.correction_logger import DataCollectionLogger, CorrectionEvent


class TestCorrectionEvent:
    """Тесты для CorrectionEvent."""

    def test_correction_event_creation(self):
        """Тест создания события корректировки."""
        timestamp = datetime.now()
        event = CorrectionEvent(
            timestamp=timestamp,
            dxf_file="test.dxf",
            operator_id="operator1",
            correction_type="position",
            affected_pieces=["piece1", "piece2"],
            before_state={"x": 100, "y": 200},
            after_state={"x": 110, "y": 210},
            reason="Optimization",
            improvement_score=0.8,
        )

        assert event.timestamp == timestamp
        assert event.dxf_file == "test.dxf"
        assert event.operator_id == "operator1"
        assert event.correction_type == "position"
        assert event.affected_pieces == ["piece1", "piece2"]
        assert event.before_state == {"x": 100, "y": 200}
        assert event.after_state == {"x": 110, "y": 210}
        assert event.reason == "Optimization"
        assert event.improvement_score == 0.8


class TestDataCollectionLogger:
    """Тесты для DataCollectionLogger."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.test_log_dir = Path("test_logs")
        self.test_log_dir.mkdir(exist_ok=True)
        self.logger = DataCollectionLogger(self.test_log_dir)

    def teardown_method(self):
        """Очистка после каждого теста."""
        import shutil

        if self.test_log_dir.exists():
            shutil.rmtree(self.test_log_dir)

    def test_initialization(self):
        """Тест инициализации логгера."""
        assert self.logger.log_dir == self.test_log_dir
        assert self.test_log_dir.exists()
        assert self.logger.logger is not None

    def test_log_correction(self):
        """Тест логирования корректировки."""
        event = CorrectionEvent(
            timestamp=datetime.now(),
            dxf_file="test.dxf",
            operator_id="operator1",
            correction_type="position",
            affected_pieces=["piece1", "piece2"],
            before_state={"x": 100, "y": 200},
            after_state={"x": 110, "y": 210},
            reason="Optimization",
            improvement_score=0.8,
        )

        # Логируем корректировку
        self.logger.log_correction(event)

        # Проверяем, что файл лога создан
        log_files = list(self.test_log_dir.glob("*.log"))
        assert len(log_files) > 0

        # Проверяем, что JSON файл с деталями создан
        json_files = list(self.test_log_dir.glob("correction_*.json"))
        assert len(json_files) > 0

        # Проверяем содержимое JSON файла
        with open(json_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["dxf_file"] == "test.dxf"
            assert data["operator_id"] == "operator1"
            assert data["correction_type"] == "position"
            assert data["affected_pieces"] == ["piece1", "piece2"]
            assert data["reason"] == "Optimization"
            assert data["improvement_score"] == 0.8

    def test_log_processing_step(self):
        """Тест логирования шага обработки."""
        details = {"step": "parsing", "file": "test.dxf", "entities_count": 10}

        self.logger.log_processing_step("DXF Parsing", details)

        # Проверяем, что лог создан
        log_files = list(self.test_log_dir.glob("*.log"))
        assert len(log_files) > 0

    def test_log_batch_produced(self):
        """Тест логирования создания партии данных."""
        self.logger.log_batch_produced("batch_001", 100)

        # Проверяем, что лог создан
        log_files = list(self.test_log_dir.glob("*.log"))
        assert len(log_files) > 0

    def test_log_error(self):
        """Тест логирования ошибки."""
        context = {"file": "test.dxf", "error_type": "parsing_error"}

        self.logger.log_error(
            "ParsingError", "Failed to parse DXF file", context
        )

        # Проверяем, что лог создан
        log_files = list(self.test_log_dir.glob("*.log"))
        assert len(log_files) > 0

    def test_get_corrections_summary(self):
        """Тест получения сводки по корректировкам."""
        summary = self.logger.get_corrections_summary(days=30)

        assert "period_days" in summary
        assert "total_corrections" in summary
        assert "by_type" in summary
        assert "average_improvement" in summary
        assert "top_operators" in summary
        assert summary["period_days"] == 30
        assert summary["total_corrections"] == 0  # Пока нет данных

    def test_export_corrections_for_analysis(self):
        """Тест экспорта корректировок для анализа."""
        output_path = self.test_log_dir / "corrections_export.json"

        exported_path = self.logger.export_corrections_for_analysis(
            output_path, days=30
        )

        assert exported_path.exists()
        assert exported_path.name == "corrections_export.json"

        # Проверяем содержимое файла
        with open(exported_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "export_date" in data
            assert "period_days" in data
            assert "corrections" in data
            assert data["period_days"] == 30

    def test_get_statistics(self):
        """Тест получения статистики сбора данных."""
        stats = self.logger.get_statistics()

        assert "total_logged_events" in stats
        assert "corrections_by_type" in stats
        assert "average_improvement_score" in stats
        assert "most_active_operators" in stats
        assert "processing_errors" in stats
        assert "data_quality_score" in stats

    def test_cleanup_old_logs(self):
        """Тест очистки старых логов."""
        deleted_count = self.logger.cleanup_old_logs(days_to_keep=90)

        assert isinstance(deleted_count, int)
        assert deleted_count >= 0

    def test_save_correction_details(self):
        """Тест сохранения деталей корректировки."""
        event = CorrectionEvent(
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            dxf_file="test.dxf",
            operator_id="operator1",
            correction_type="position",
            affected_pieces=["piece1"],
            before_state={"x": 100},
            after_state={"x": 110},
            reason="Test",
            improvement_score=0.5,
        )

        filepath = self.logger._save_correction_details(event)

        assert filepath.exists()
        assert "correction_20230101_120000_position.json" in filepath.name

        # Проверяем содержимое файла
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["dxf_file"] == "test.dxf"
            assert data["operator_id"] == "operator1"
            assert data["correction_type"] == "position"
            assert data["improvement_score"] == 0.5

    def test_logger_with_existing_directory(self):
        """Тест инициализации логгера с существующей директорией."""
        # Создаем директорию заранее
        existing_dir = Path("existing_logs")
        existing_dir.mkdir(exist_ok=True)

        try:
            logger = DataCollectionLogger(existing_dir)
            assert logger.log_dir == existing_dir
            assert existing_dir.exists()
        finally:
            import shutil

            if existing_dir.exists():
                shutil.rmtree(existing_dir)

    def test_multiple_corrections_logging(self):
        """Тест логирования множественных корректировок."""
        events = [
            CorrectionEvent(
                timestamp=datetime.now(),
                dxf_file="test1.dxf",
                operator_id="operator1",
                correction_type="position",
                affected_pieces=["piece1"],
                before_state={"x": 100},
                after_state={"x": 110},
                reason="Test 1",
                improvement_score=0.6,
            ),
            CorrectionEvent(
                timestamp=datetime.now(),
                dxf_file="test2.dxf",
                operator_id="operator2",
                correction_type="rotation",
                affected_pieces=["piece2"],
                before_state={"angle": 0},
                after_state={"angle": 90},
                reason="Test 2",
                improvement_score=0.8,
            ),
        ]

        # Логируем обе корректировки
        for event in events:
            self.logger.log_correction(event)

        # Проверяем, что созданы файлы для обеих корректировок
        json_files = list(self.test_log_dir.glob("correction_*.json"))
        assert len(json_files) >= 2
