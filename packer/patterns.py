import os
from .config import logger


def get_bounding_box(doc):
    """
    Заглушка для получения ограничивающего прямоугольника

    Args:
        doc: DXF документ

    Returns:
        tuple: ((0, 0), 0, 0) - заглушка
    """
    return (0, 0), 0, 0


def load_and_convert_pattern(pattern_path):
    """
    Заглушка для загрузки DXF файла узора

    Args:
        pattern_path: путь к DXF файлу узора

    Returns:
        tuple: (None, 0, 0) - заглушка
    """
    logger.info(f"Загрузка узора отключена: {pattern_path}")
    return None, 0, 0


def load_patterns(pattern_dir):
    """
    Заглушка для загрузки всех DXF файлов узоров

    Args:
        pattern_dir: директория с DXF файлами узоров

    Returns:
        dict: {} - пустой словарь
    """
    logger.info(
        f"Папка с узорами: {pattern_dir} (функциональность загрузки узоров отключена)")

    # Создаем директорию, если она не существует
    if not os.path.exists(pattern_dir):
        os.makedirs(pattern_dir)
        logger.info(f"Создана директория для узоров: {pattern_dir}")

    return {}
