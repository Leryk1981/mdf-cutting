# Константы приложения

# Стандартные размеры листа
STANDARD_SHEET_LENGTH = 2800
STANDARD_SHEET_WIDTH = 2070
STANDARD_SHEET_AREA = STANDARD_SHEET_LENGTH * STANDARD_SHEET_WIDTH

# Обязательные колонки в файлах
MATERIALS_REQUIRED_COLUMNS = [
    'thickness_mm',
    'material',
    'sheet_length_mm',
    'sheet_width_mm',
    'total_quantity',
    'is_remnant'
]

DETAILS_REQUIRED_COLUMNS = [
    'part_id',
    'order_id',
    'length_mm',
    'width_mm',
    'quantity',
    'thickness_mm',
    'material',
    'milling_type',
    'bevel_type',
    'bevel_offset_mm',
    'f_long',
    'f_short'
]

# Определение типа материала


def is_remnant(length, width):
    """Определяет, является ли материал остатком"""
    return (length < STANDARD_SHEET_LENGTH or width < STANDARD_SHEET_WIDTH)


# Стандартные значения
DEFAULT_TOOL_DIAMETER = 4  # мм
DEFAULT_TRIM = 6  # мм
DEFAULT_MARGIN = 6  # мм
DEFAULT_KERF = 4  # мм


# Поддерживаемые кодировки
SUPPORTED_ENCODINGS = ['utf-8', 'utf-8-sig', 'windows-1251']
