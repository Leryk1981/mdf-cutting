"""
Утилиты для работы с файлами.

Этот модуль содержит:
- Безопасные имена файлов
- Создание резервных копий
- Проверку существования файлов
- Работу с путями
"""

import os
import shutil
from typing import Optional


def safe_filename(filename: str) -> str:
    """
    Создает безопасное имя файла.

    Убирает недопустимые символы и заменяет их на подчеркивания.

    Args:
        filename: Исходное имя файла

    Returns:
        str: Безопасное имя файла
    """
    # Заменяем недопустимые символы
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Убираем множественные подчеркивания
    while "__" in filename:
        filename = filename.replace("__", "_")

    return filename


def create_backup(file_path: str, backup_dir: Optional[str] = None) -> str:
    """
    Создает резервную копию файла.

    Args:
        file_path: Путь к файлу для резервного копирования
        backup_dir: Директория для резервных копий (опционально)

    Returns:
        str: Путь к созданной резервной копии
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    # Определяем директорию для резервных копий
    if backup_dir is None:
        backup_dir = os.path.dirname(file_path)

    # Создаем имя резервной копии
    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)
    backup_name = f"{name}_backup{ext}"
    backup_path = os.path.join(backup_dir, backup_name)

    # Создаем резервную копию
    shutil.copy2(file_path, backup_path)

    return backup_path
