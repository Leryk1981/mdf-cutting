import ezdxf
from ezdxf.enums import TextEntityAlignment

# TODO: Consider moving DEFAULT_TEXT_STYLE, DEFAULT_TEXT_HEIGHT, HEADER_TEXT_HEIGHT, BORDER_COLOR, TEXT_COLOR, DETAIL_TEXT_COLOR, DIMENSION_COLOR from constants.py
# if they are only used here. For now, keeping them in constants.py for broader use.
from .constants import (
    DEFAULT_TEXT_STYLE,
    DEFAULT_TEXT_HEIGHT,
    HEADER_TEXT_HEIGHT,
    BORDER_COLOR,
    TEXT_COLOR,
    DETAIL_TEXT_COLOR,
    DIMENSION_COLOR # Assuming DIMENSION_COLOR might be used for dimensions if added later
)

def create_new_dxf():
    """Создает новый DXF документ и возвращает его и пространство модели."""
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    # Установка единиц измерения в миллиметры
    doc.header['$LUNITS'] = 2  # 2 for decimal
    doc.header['$INSUNITS'] = 4 # 4 for Millimeters
    return doc, msp

def add_sheet_outline(msp, sheet_length, sheet_width, margin):
    """Добавляет контур листа и рабочую зону в DXF."""
    # Внешний контур листа
    msp.add_lwpolyline(
        [(0, 0), (sheet_length, 0), (sheet_length, sheet_width), (0, sheet_width), (0, 0)],
        dxfattribs={'color': BORDER_COLOR, 'layer': 'Sheet Outline'}
    )
    # Рабочая зона с учетом отступов
    msp.add_lwpolyline(
        [(margin, margin), (sheet_length - margin, margin),
         (sheet_length - margin, sheet_width - margin), (margin, sheet_width - margin), (margin, margin)],
        dxfattribs={'color': BORDER_COLOR, 'linetype': 'DASHED', 'layer': 'Working Area'}
    )

def add_detail_to_sheet(msp, detail, detail_rect, kerf):
    """
    Добавляет деталь на лист DXF и возвращает информацию о ней.

    Args:
        msp: Пространство модели DXF.
        detail: Словарь с информацией о детали (part_id, length_mm, width_mm).
        detail_rect: Словарь с координатами и размерами упакованной детали
                     {'x', 'y', 'width', 'height', 'rotated'}.
                     x, y - координаты нижнего левого угла детали С УЧЕТОМ margin.
                     width, height - размеры детали С УЧЕТОМ kerf.
        kerf: Диаметр фрезы (мм).

    Returns:
        dict: Информация о детали для списка (имя, размеры).
    """
    part_id = detail['part_id']
    # Размеры детали БЕЗ учета kerf (фактические размеры детали)
    actual_length = detail_rect['width'] - kerf  # rect.width includes kerf
    actual_width = detail_rect['height'] - kerf # rect.height includes kerf

    # Координаты нижнего левого угла детали (уже включают margin)
    x_coord = detail_rect['x']
    y_coord = detail_rect['y']

    # Добавляем контур детали
    msp.add_lwpolyline(
        [(x_coord, y_coord), (x_coord + actual_length, y_coord),
         (x_coord + actual_length, y_coord + actual_width),
         (x_coord, y_coord + actual_width), (x_coord, y_coord)],
        dxfattribs={'color': TEXT_COLOR, 'layer': 'Details'}
    )

    # Добавляем ID детали и ее размеры
    text_content = f"{part_id} ({actual_length:.0f}x{actual_width:.0f})"
    text_x = x_coord + actual_length / 2
    text_y = y_coord + actual_width / 2

    msp.add_text(
        text_content,
        dxfattribs={
            'style': DEFAULT_TEXT_STYLE,
            'height': DEFAULT_TEXT_HEIGHT,
            'color': DETAIL_TEXT_COLOR,
            'layer': 'Detail Text'
        }
    ).set_placement(
        (text_x, text_y),
        align=TextEntityAlignment.MIDDLE_CENTER
    )
    return {'name': part_id, 'size': f"{actual_length:.0f}x{actual_width:.0f}"}

def add_layout_filename_title(msp, sheet_length, sheet_width, filename_text):
    """Добавляет имя файла карты раскроя в DXF."""
    msp.add_text(
        filename_text,
        dxfattribs={
            'style': DEFAULT_TEXT_STYLE,
            'height': HEADER_TEXT_HEIGHT,  # Используем высоту для заголовка
            'color': TEXT_COLOR,
            'layer': 'Title'
        }
    ).set_placement(
        (sheet_length / 2, sheet_width + HEADER_TEXT_HEIGHT * 2), # Размещаем над листом
        align=TextEntityAlignment.MIDDLE_CENTER
    )

def add_details_list(msp, sheet_width, details_list, list_position_y=None, text_height=None):
    """
    Добавляет список деталей на лист DXF.

    Args:
        msp: Пространство модели DXF.
        sheet_width: Ширина листа (для позиционирования списка).
        details_list: Список словарей с информацией о деталях [{'name': str, 'size': str}].
        list_position_y: Опциональная Y-координата для начала списка. Если None, используется позиция под листом.
        text_height: Опциональная высота текста для списка. Если None, используется DEFAULT_TEXT_HEIGHT.
    """
    if text_height is None:
        text_height = DEFAULT_TEXT_HEIGHT # Стандартная высота текста для списка

    # Начальная позиция для списка деталей
    # Если list_position_y не задан, размещаем под листом с небольшим отступом
    if list_position_y is None:
        current_y = - (text_height * (len(details_list) + 2)) # Позиция под листом
    else:
        current_y = list_position_y

    # Добавляем заголовок списка
    msp.add_text(
        "Список деталей:",
        dxfattribs={
            'style': DEFAULT_TEXT_STYLE,
            'height': text_height, # Используем заданную или стандартную высоту
            'color': TEXT_COLOR,
            'layer': 'Details List'
        }
    ).set_placement(
        (0, current_y), # Слева под листом или в указанной позиции
        align=TextEntityAlignment.BOTTOM_LEFT
    )
    current_y -= text_height * 1.5 # Отступ после заголовка

    # Добавляем каждую деталь в список
    for detail_item in details_list:
        item_text = f"{detail_item['name']} - {detail_item['size']}"
        msp.add_text(
            item_text,
            dxfattribs={
                'style': DEFAULT_TEXT_STYLE,
                'height': text_height, # Используем заданную или стандартную высоту
                'color': TEXT_COLOR,
                'layer': 'Details List'
            }
        ).set_placement(
            (0, current_y),
            align=TextEntityAlignment.BOTTOM_LEFT
        )
        current_y -= text_height # Сдвиг для следующей строки
