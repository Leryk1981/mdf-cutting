"""
Система логирования сбора данных для AI-системы.

Этот модуль содержит:
- Логирование ручных корректировок карт раскроя
- Структурированное хранение событий
- Анализ эффективности корректировок
- Экспорт данных для анализа
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class CorrectionEvent:
    """Структура для записи события корректировки."""

    timestamp: datetime
    dxf_file: str
    operator_id: str
    correction_type: str  # "position", "rotation", "dimension_change", "custom"
    affected_pieces: List[str]
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    reason: str
    improvement_score: float  # Оценка улучшения от корректировки


class DataCollectionLogger:
    """
    Логгер для сбора данных о корректировках.

    Обеспечивает структурированное логирование событий корректировки
    карт раскроя для последующего анализа и обучения AI-моделей.
    """

    def __init__(self, log_dir: Path):
        """
        Инициализация логгера.

        Args:
            log_dir: Директория для логов
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Настраиваем логгер
        self.logger = logging.getLogger("data_collection")
        self.logger.setLevel(logging.INFO)

        # Очищаем существующие обработчики
        self.logger.handlers.clear()

        # Форматтер
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Файловый обработчик
        file_handler = logging.FileHandler(
            self.log_dir
            / f"data_collection_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Консольный обработчик (для отладки)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def log_correction(self, correction: CorrectionEvent) -> None:
        """
        Зарегистрировать корректировку карты.

        Args:
            correction: Событие корректировки
        """
        # Логируем в общий лог
        self.logger.info(
            f"Correction logged: {correction.correction_type} on "
            f"{correction.dxf_file} by {correction.operator_id} - "
            f"Score improvement: {correction.improvement_score:.2f}"
        )

        # Сохраняем детальную информацию в JSON
        self._save_correction_details(correction)

    def log_processing_step(self, step: str, details: Dict[str, Any]) -> None:
        """
        Зарегистрировать шаг обработки данных.

        Args:
            step: Название шага
            details: Детали обработки
        """
        self.logger.info(f"Processing step: {step}")
        if details:
            self.logger.debug(
                f"Details: {json.dumps(details, ensure_ascii=False)}"
            )

    def log_batch_produced(self, batch_id: str, sample_count: int) -> None:
        """
        Зарегистрировать создание партии данных для обучения.

        Args:
            batch_id: ID партии
            sample_count: Количество образцов
        """
        self.logger.info(
            f"Training batch produced: {batch_id} with {sample_count} samples"
        )

    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Dict[str, Any] = None
    ) -> None:
        """
        Зарегистрировать ошибку обработки.

        Args:
            error_type: Тип ошибки
            error_message: Сообщение об ошибке
            context: Контекст ошибки
        """
        self.logger.error(f"Error {error_type}: {error_message}")
        if context:
            self.logger.debug(
                f"Error context: {json.dumps(context, ensure_ascii=False)}"
            )

    def get_corrections_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Получить сводку по корректировкам за N дней.

        Args:
            days: Количество дней для анализа

        Returns:
            Dict: Сводка по корректировкам
        """
        # В реальной реализации здесь может быть анализ логов
        # Пока возвращаем базовую структуру
        return {
            "period_days": days,
            "total_corrections": 0,  # Будет рассчитано
            "by_type": {
                "position": 0,
                "rotation": 0,
                "dimension_change": 0,
                "custom": 0,
            },
            "average_improvement": 0.0,
            "top_operators": [],
            "most_corrected_files": [],
            "improvement_trend": [],
        }

    def export_corrections_for_analysis(
        self, output_path: Path, days: int = 30
    ) -> Path:
        """
        Экспортировать корректировки для анализа.

        Args:
            output_path: Путь для экспорта
            days: Количество дней для экспорта

        Returns:
            Path: Путь к экспортированному файлу
        """
        # В реальной реализации здесь может быть экспорт в CSV/JSON
        corrections_data = {
            "export_date": datetime.now().isoformat(),
            "period_days": days,
            "corrections": [],  # Будет заполнено из логов
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(corrections_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Corrections exported to {output_path}")
        return output_path

    def _save_correction_details(self, correction: CorrectionEvent) -> Path:
        """
        Сохранить детали корректировки в отдельный файл.

        Args:
            correction: Событие корректировки

        Returns:
            Path: Путь к сохраненному файлу
        """
        timestamp_str = correction.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = (
            f"correction_{timestamp_str}_{correction.correction_type}.json"
        )
        filepath = self.log_dir / filename

        # Преобразуем datetime в строку для JSON
        correction_dict = asdict(correction)
        correction_dict["timestamp"] = correction_dict["timestamp"].isoformat()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(correction_dict, f, indent=2, ensure_ascii=False)

        self.logger.debug(f"Correction details saved to {filepath}")
        return filepath

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику сбора данных.

        Returns:
            Dict: Статистика сбора данных
        """
        return {
            "total_logged_events": 0,  # Будет рассчитано
            "corrections_by_type": {},
            "average_improvement_score": 0.0,
            "most_active_operators": [],
            "processing_errors": 0,
            "data_quality_score": 0.0,
        }

    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Очистить старые логи.

        Args:
            days_to_keep: Количество дней для хранения

        Returns:
            int: Количество удаленных файлов
        """
        # В реальной реализации здесь может быть очистка старых файлов
        self.logger.info(
            f"Cleanup requested: keeping logs for {days_to_keep} days"
        )
        return 0  # Будет рассчитано
