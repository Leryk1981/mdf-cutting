import logging

# Файл логирования
LOG_FILE = "packer.log"

# Настройка логирования


def setup_logging():
    """Настраивает логирование приложения"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logger = logging.getLogger("packer")
    logger.setLevel(logging.INFO)

    # Удаляем все существующие обработчики логов
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    # Добавляем файловый обработчик
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="w")
    file_handler.setFormatter(logging.Formatter(log_format))

    # Добавляем консольный обработчик
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(log_format))

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


logger = logging.getLogger("packer")
