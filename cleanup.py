import os
import glob
from .config import logger, LOG_FILE


class CleanupManager:
    """Менеджер очистки временных файлов"""

    def __init__(self):
        self.temp_patterns = ["*.log", "*.tmp", "intermediate_*.dxf"]
        self.output_patterns = ["final_layout_*.dxf"]

    def cleanup_logs(self):
        """Очищает файлы логов"""
        try:
            logger.info("Очистка логов...")
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'w', encoding='utf-8') as f:
                    f.write('')
                logger.info(f"Лог-файл {LOG_FILE} очищен")
        except Exception as e:
            logger.error(f"Ошибка при очистке логов: {str(e)}")

    def cleanup_temp_files(self):
        """Очищает временные файлы"""
        try:
            logger.info("Очистка временных файлов...")
            for pattern in self.temp_patterns:
                for file_path in glob.glob(pattern):
                    try:
                        os.remove(file_path)
                        logger.info(f"Удален файл: {file_path}")
                    except Exception as e:
                        logger.warning(
                            f"Не удалось удалить файл {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка при очистке временных файлов: {str(e)}")

    def cleanup_output_files(self):
        """Очищает файлы результатов"""
        try:
            logger.info("Очистка выходных файлов...")
            for pattern in self.output_patterns:
                for file_path in glob.glob(pattern):
                    try:
                        os.remove(file_path)
                        logger.info(f"Удален файл: {file_path}")
                    except Exception as e:
                        logger.warning(
                            f"Не удалось удалить файл {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка при очистке выходных файлов: {str(e)}")

    def cleanup_all(self, keep_output=True):
        """
        Очищает все временные файлы

        Args:
            keep_output: сохранять файлы результатов
        """
        self.cleanup_temp_files()
        if not keep_output:
            self.cleanup_output_files()