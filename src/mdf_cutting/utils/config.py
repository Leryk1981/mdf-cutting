"""
Конфигурация системы логирования.

Этот модуль содержит:
- Настройку логирования
- Конфигурационные параметры
- Утилиты для работы с конфигурацией
"""

import logging
from typing import Optional


def setup_logging(
    level: str = "INFO", log_file: Optional[str] = None
) -> logging.Logger:
    """
    Настройка системы логирования.

    Args:
        level: Уровень логирования
        log_file: Путь к файлу логов (опционально)

    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger("mdf_cutting")
    logger.setLevel(getattr(logging, level.upper()))

    # Создаем форматтер
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Добавляем обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Добавляем обработчик для файла если указан
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Создаем основной логгер
logger = setup_logging()
