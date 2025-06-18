import logging
import pandas as pd
import re
from .config import logger


def set_log_level(level_name):
    """Устанавливает уровень логирования"""
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = levels.get(level_name.upper(), logging.INFO)
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
    logger.info(f"Уровень логирования изменен на: {level_name}")


def read_csv_files(details_path, materials_path, encodings):
    """
    Читает CSV файлы с данными деталей и материалов

    Args:
        details_path: путь к файлу с деталями
        materials_path: путь к файлу с материалами
        encodings: список кодировок для попытки чтения

    Returns:
        tuple: (details_df, materials_df) или (None, None) при ошибке
    """
    details_df = None
    materials_df = None

    # Пытаемся прочитать файлы с различными кодировками
    for encoding in encodings:
        try:
            # Чтение с параметром low_memory=False для полной загрузки данных
            details_df = pd.read_csv(details_path, sep=';', encoding=encoding, low_memory=False,
                                     dtype={'order_id': str, 'bevel_type': str, 'thickness_mm': float, 'material': str})
            materials_df = pd.read_csv(materials_path, sep=';', encoding=encoding, low_memory=False,
                                       dtype={'thickness_mm': float, 'material': str})
            logger.info(f"Успешно прочитаны файлы с кодировкой: {encoding}")

            # Проверим, получены ли поля корректно
            if details_df is not None:
                logger.info(
                    f"Пример значений bevel_type: {details_df['bevel_type'].unique()[:5] if 'bevel_type' in details_df.columns else 'Колонка не найдена'}")
                logger.info(
                    f"Пример значений order_id: {details_df['order_id'].unique()[:5] if 'order_id' in details_df.columns else 'Колонка не найдена'}")
                logger.info(
                    f"Пример значений material: {details_df['material'].unique()[:5] if 'material' in details_df.columns else 'Колонка не найдена'}")

            if materials_df is not None:
                logger.info(
                    f"Пример значений материалов: {materials_df['material'].unique()[:5] if 'material' in materials_df.columns else 'Колонка не найдена'}")

            break
        except Exception as e:
            logger.warning(f"Ошибка чтения с кодировкой {encoding}: {str(e)}")
            continue

    # Проверяем наличие колонки material и добавляем, если её нет
    if details_df is not None and 'material' not in details_df.columns:
        details_df['material'] = 'S'  # S - стандартный материал по умолчанию
        logger.info(
            "Колонка 'material' добавлена в таблицу деталей со значением 'S' по умолчанию")

    if materials_df is not None and 'material' not in materials_df.columns:
        materials_df['material'] = 'S'  # S - стандартный материал по умолчанию
        logger.info(
            "Колонка 'material' добавлена в таблицу материалов со значением 'S' по умолчанию")

    # Преобразование старых названий колонок в новые
    if details_df is not None:
        # Преобразуем f_длина в f_long, если нужно
        if 'f_длина' in details_df.columns and 'f_long' not in details_df.columns:
            details_df['f_long'] = details_df['f_длина']
            logger.info("Колонка 'f_длина' преобразована в 'f_long'")

        # Преобразуем f_ширина в f_short, если нужно
        if 'f_ширина' in details_df.columns and 'f_short' not in details_df.columns:
            details_df['f_short'] = details_df['f_ширина']
            logger.info("Колонка 'f_ширина' преобразована в 'f_short'")

    return details_df, materials_df


def validate_dataframes(details_df, materials_df, details_req_cols, materials_req_cols):
    """
    Проверяет наличие всех необходимых колонок в DataFrame

    Args:
        details_df: DataFrame с деталями
        materials_df: DataFrame с материалами
        details_req_cols: список обязательных колонок для деталей
        materials_req_cols: список обязательных колонок для материалов

    Returns:
        tuple: (is_valid, missing_cols_details, missing_cols_materials)
    """
    # Добавляем 'material' в список обязательных колонок, если её там нет
    if 'material' not in details_req_cols:
        details_req_cols = details_req_cols + ['material']

    if 'material' not in materials_req_cols:
        materials_req_cols = materials_req_cols + ['material']

    # Проверяем наличие старых названий колонок для совместимости
    # Если есть старое название, но нет нового, считаем что колонка есть
    alt_columns = {
        'f_long': 'f_длина',
        'f_short': 'f_ширина'
    }

    missing_cols_details = []
    for col in details_req_cols:
        if col not in details_df.columns:
            # Проверяем, есть ли альтернативное имя колонки
            alt_col = alt_columns.get(col)
            if alt_col and alt_col in details_df.columns:
                continue  # Считаем, что колонка есть
            missing_cols_details.append(col)

    missing_cols_materials = [
        col for col in materials_req_cols if col not in materials_df.columns
    ]

    is_valid = not (missing_cols_details or missing_cols_materials)
    return is_valid, missing_cols_details, missing_cols_materials


def preprocess_dataframes(details_df, materials_df):
    """
    Предобработка DataFrame с деталями и материалами

    Args:
        details_df: DataFrame с деталями
        materials_df: DataFrame с материалами

    Returns:
        tuple: (processed_details_df, processed_materials_df)
    """
    try:
        # Создаем копии для обработки
        details_df = details_df.copy()
        materials_df = materials_df.copy()

        # Преобразуем старые имена колонок в новые, если нужно
        if 'f_длина' in details_df.columns and 'f_long' not in details_df.columns:
            details_df['f_long'] = details_df['f_длина']

        if 'f_ширина' in details_df.columns and 'f_short' not in details_df.columns:
            details_df['f_short'] = details_df['f_ширина']

        # Удаляем старые колонки, если есть и новые колонки
        if 'f_длина' in details_df.columns and 'f_long' in details_df.columns:
            details_df = details_df.drop(columns=['f_длина'])

        if 'f_ширина' in details_df.columns and 'f_short' in details_df.columns:
            details_df = details_df.drop(columns=['f_ширина'])

        # Проверяем наличие колонки material и добавляем стандартное значение, если её нет
        if 'material' not in details_df.columns:
            details_df['material'] = 'S'
            logger.info(
                "Добавлена колонка 'material' в таблицу деталей со значением 'S' по умолчанию")

        if 'material' not in materials_df.columns:
            materials_df['material'] = 'S'
            logger.info(
                "Добавлена колонка 'material' в таблицу материалов со значением 'S' по умолчанию")

        # Приводим material к верхнему регистру для консистентности
        details_df['material'] = details_df['material'].astype(str).str.upper()
        materials_df['material'] = materials_df['material'].astype(
            str).str.upper()

        # Заменяем пустые значения на 'S'
        details_df['material'] = details_df['material'].replace(
            '', 'S').fillna('S')
        materials_df['material'] = materials_df['material'].replace(
            '', 'S').fillna('S')

        # Обработка числовых колонок в details_df
        numeric_columns_details = [
            'length_mm', 'width_mm', 'quantity', 'thickness_mm',
            'bevel_offset_mm', 'f_long', 'f_short'
        ]
        for col in numeric_columns_details:
            if col in details_df.columns:
                details_df[col] = pd.to_numeric(
                    details_df[col], errors='coerce').fillna(0)

        # Приведение к целым числам где нужно
        integer_columns = ['quantity', 'f_long', 'f_short']
        for col in integer_columns:
            if col in details_df.columns:
                details_df[col] = details_df[col].astype(int)

        # Обработка числовых колонок в materials_df
        numeric_columns_materials = [
            'sheet_length_mm', 'sheet_width_mm',
            'total_quantity', 'thickness_mm'
        ]
        for col in numeric_columns_materials:
            if col in materials_df.columns:
                materials_df[col] = pd.to_numeric(
                    materials_df[col], errors='coerce')

        # Приведение к целым числам где нужно
        if 'total_quantity' in materials_df.columns:
            materials_df['total_quantity'] = materials_df['total_quantity'].astype(
                int)

        # Проверяем, что толщины имеют корректные значения
        if 'thickness_mm' in details_df.columns and (details_df['thickness_mm'] <= 0).any():
            logger.warning(
                "Обнаружены неположительные значения толщины в таблице деталей")

        if 'thickness_mm' in materials_df.columns and (materials_df['thickness_mm'] <= 0).any():
            logger.warning(
                "Обнаружены неположительные значения толщины в таблице материалов")

        return details_df, materials_df

    except Exception as e:
        logger.error(f"Ошибка при предобработке данных: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None


def check_critical_values(details_df, materials_df):
    """
    Проверяет критические значения в DataFrame

    Args:
        details_df: DataFrame с деталями
        materials_df: DataFrame с материалами

    Returns:
        bool: True если данные корректны
    """
    # Проверка на пустые значения в важных колонках
    critical_columns_details = ['length_mm',
                                'width_mm', 'quantity', 'thickness_mm', 'material']
    critical_columns_materials = [
        'sheet_length_mm', 'sheet_width_mm', 'total_quantity', 'thickness_mm', 'material'
    ]

    if details_df[critical_columns_details].isnull().any().any():
        logger.error(
            "Обнаружены пустые значения в важных колонках таблицы деталей")
        return False

    if materials_df[critical_columns_materials].isnull().any().any():
        logger.error(
            "Обнаружены пустые значения в важных колонках таблицы материалов")
        return False

    # Проверка на отрицательные значения для числовых колонок
    if (details_df[['length_mm', 'width_mm', 'quantity']] < 0).any().any():
        logger.error(
            "Обнаружены отрицательные значения в размерах или количестве деталей")
        return False

    if (materials_df[['sheet_length_mm', 'sheet_width_mm', 'total_quantity']] < 0).any().any():
        logger.error(
            "Обнаружены отрицательные значения в размерах или количестве листов")
        return False

    return True


def prepare_materials_df(materials_df):
    """Подготовка таблицы материалов"""
    if 'is_remnant' not in materials_df.columns:
        materials_df['is_remnant'] = materials_df.apply(
            lambda row: is_remnant(
                row['sheet_length_mm'], row['sheet_width_mm']),
            axis=1
        )

    # Приводим material к верхнему регистру для консистентности
    materials_df['material'] = materials_df['material'].astype(str).str.upper()

    return materials_df


def load_and_prepare_data(details_path, materials_path, details_required_cols,
                          materials_required_cols, supported_encodings):
    """
    Orchestrates the loading and preparation of details and materials data.

    This function calls the following sequence of operations:
    1. read_csv_files: Reads data from CSV files.
    2. validate_dataframes: Validates that necessary columns are present.
    3. preprocess_dataframes: Cleans and transforms data (e.g., type conversion, handling missing values).
    4. check_critical_values: Checks for values that would prevent further processing (e.g., negative dimensions).

    Args:
        details_path (str): Path to the details CSV file.
        materials_path (str): Path to the materials CSV file.
        details_required_cols (list[str]): List of required column names for the details DataFrame.
        materials_required_cols (list[str]): List of required column names for the materials DataFrame.
        supported_encodings (list[str]): List of encodings to try when reading CSV files.

    Returns:
        tuple: (details_df, materials_df, error_message)
               - details_df (pd.DataFrame | None): Processed details DataFrame, or None if an error occurred.
               - materials_df (pd.DataFrame | None): Processed materials DataFrame, or None if an error occurred.
               - error_message (str | None): An error message string if any step failed, otherwise None.
    """
    logger.info("Starting data loading and preparation process.")

    # 1. Read CSV files
    details_df, materials_df = read_csv_files(details_path, materials_path, supported_encodings)
    if details_df is None or materials_df is None:
        error_msg = "Failed to read one or both CSV files. Check logs for details on encodings."
        logger.error(error_msg)
        return None, None, error_msg

    logger.info("Successfully read CSV files.")

    # 2. Validate DataFrames
    is_valid, missing_cols_details, missing_cols_materials = validate_dataframes(
        details_df, materials_df, details_required_cols, materials_required_cols
    )
    if not is_valid:
        error_parts = []
        if missing_cols_details:
            error_parts.append(f"Missing in details file: {', '.join(missing_cols_details)}")
        if missing_cols_materials:
            error_parts.append(f"Missing in materials file: {', '.join(missing_cols_materials)}")
        error_msg = "Data validation failed. Required columns are missing. " + "; ".join(error_parts)
        logger.error(error_msg)
        return None, None, error_msg

    logger.info("Successfully validated DataFrame columns.")

    # 3. Preprocess DataFrames
    details_df, materials_df = preprocess_dataframes(details_df, materials_df)
    if details_df is None or materials_df is None:
        error_msg = "Data preprocessing failed. Check logs for details."
        logger.error(error_msg)
        # preprocess_dataframes logs the specific error, so a generic message here is okay.
        return None, None, error_msg

    logger.info("Successfully preprocessed DataFrames.")

    # 4. Check Critical Values
    if not check_critical_values(details_df, materials_df):
        # check_critical_values logs the specific error.
        error_msg = "Critical value check failed. Invalid data detected (e.g., nulls, negative dimensions). Check logs."
        logger.error(error_msg)
        return None, None, error_msg

    logger.info("Successfully passed critical value checks.")
    logger.info("Data loading and preparation completed successfully.")
    return details_df, materials_df, None
