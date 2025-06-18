import os
import logging

# Файл логирования
LOG_FILE = 'packer.log'

# Флаг для отслеживания инициализации логирования
_logging_configured = False

# Настройка логирования
logger = logging.getLogger('packer') # Define logger globally once

def setup_logging():
    """
    Настраивает логирование приложения.
    Гарантирует, что основная настройка (очистка и добавление обработчиков)
    выполняется только один раз, даже если функция вызывается многократно.
    """
    global _logging_configured
    global logger # Ensure we are modifying the global logger

    if _logging_configured:
        # logger.debug("Logging already configured.") # Optional: for debugging multiple calls
        return logger

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger.setLevel(logging.INFO) # Set default level for the logger itself

    # Удаляем все существующие обработчики логов, чтобы избежать дублирования
    # при случайном повторном вызове (хотя флаг должен это предотвратить)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    # Добавляем файловый обработчик
    try:
        file_handler = logging.FileHandler(
            LOG_FILE, encoding='utf-8', mode='w') # 'w' to overwrite log on each run
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to console if file logging fails
        print(f"Error setting up file logger: {e}. Logging to console only.")


    # Добавляем консольный обработчик (StreamHandler)
    # Этот обработчик будет выводить логи в sys.stdout/sys.stderr,
    # что позволяет GUI перехватывать их через TextRedirector.
    stream_handler = logging.StreamHandler() # Defaults to sys.stderr
    stream_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(stream_handler)

    _logging_configured = True
    logger.info("Logging setup complete.") # Initial log message
    return logger

# logger = logging.getLogger('packer') # Moved to be defined before setup_logging
