import os

from .config import logger


def create_material_folder_structure(thickness, material, base_output_dir=""):
    """
    Создает структуру папок для материала с заданной толщиной.

    Args:
        thickness: толщина материала (мм)
        material: материал (S, V, и т.д.)
        base_output_dir: базовая директория для сохранения

    Returns:
        tuple: (путь к основной папке, путь к папке clean)
    """
    try:
        # Преобразуем thickness в целое число, если оно целое
        thickness_int = (
            int(thickness) if float(thickness).is_integer() else thickness
        )

        # Формируем название папки
        if material != "S":
            folder_name = f"{thickness_int}mm_{material}"
        else:
            folder_name = f"{thickness_int}mm"

        # Полные пути к папкам
        main_folder_path = os.path.join(base_output_dir, folder_name)
        clean_folder_path = os.path.join(main_folder_path, folder_name)

        # Создаем основную папку
        os.makedirs(main_folder_path, exist_ok=True)
        logger.info(f"Создана основная папка: {main_folder_path}")

        # Создаем пустую папку clean
        os.makedirs(clean_folder_path, exist_ok=True)
        logger.info(f"Создана папка clean: {clean_folder_path}")

        return main_folder_path, clean_folder_path

    except Exception as e:
        logger.error(
            f"Ошибка при создании структуры папок для {thickness}mm_{material}: {str(e)}"
        )
        # В случае ошибки возвращаем базовую директорию
        os.makedirs(base_output_dir, exist_ok=True)
        return base_output_dir, base_output_dir


def get_organized_file_path(thickness, material, filename, base_output_dir=""):
    """
    Возвращает полный путь к файлу с учетом организации по папкам.

    Args:
        thickness: толщина материала (мм)
        material: материал (S, V, и т.д.)
        filename: имя файла
        base_output_dir: базовая директория для сохранения

    Returns:
        str: полный путь к файлу
    """
    try:
        main_folder_path, _ = create_material_folder_structure(
            thickness, material, base_output_dir
        )
        return os.path.join(main_folder_path, filename)
    except Exception as e:
        logger.error(f"Ошибка при получении пути файла: {str(e)}")
        # В случае ошибки сохраняем в базовую директорию
        os.makedirs(base_output_dir, exist_ok=True)
        return os.path.join(base_output_dir, filename)
