import ezdxf
from ezdxf.filemanagement import new
import re
import os.path
from .config import logger
from .constants import CHAMFER_TYPES


def normalize_layer_name(name):
    """
    Очищает имя слоя от недопустимых символов

    Args:
        name: исходное имя слоя

    Returns:
        str: очищенное имя слоя
    """
    if not name:
        return "UNNAMED"

    # Заменяем специальные символы на подчеркивание
    # Допустимы только буквы, цифры и некоторые спец. символы
    name = re.sub(r'[^\w\-\.]', '_', name)

    # Проверяем, что имя не пустое после очистки
    if not name or name.isspace():
        return "UNNAMED"

    return name


def add_bevels(msp, x, y, length, width, bevel_type, f_long, f_short, bevel_offset=None):
    """
    Добавляет фаски на чертеж

    Args:
        msp: modelspace DXF документа
        x, y: начальные координаты
        length, width: размеры детали
        bevel_type: тип фаски
        f_long: значения фасок по длине
        f_short: значения фасок по ширине
        bevel_offset: смещение фаски (опционально)
    """
    if not bevel_type or bevel_type.lower() in ['нет', 'none', 'no']:
        return

    # Получаем цвет по типу фаски
    if bevel_type in CHAMFER_TYPES:
        color = CHAMFER_TYPES[bevel_type]["color"]
    else:
        color = 1  # Красный по умолчанию

    # Используем смещение из таблицы, если указано
    if bevel_offset is None:
        # Если смещение не указано, используем стандартные значения
        if bevel_type in ['D', 'C', 'D_бк']:
            offset = 0.2  # Положительное смещение по умолчанию
        else:
            offset = -4.8  # Отрицательное смещение по умолчанию для типов склейка
        logger.warning(
            f"Смещение фаски не указано для {bevel_type}, используется {offset}")
    else:
        offset = bevel_offset
        logger.info(f"Используется смещение фаски из таблицы: {offset}")

    # Формируем имя слоя для этого типа фаски
    layer_name = f"CHAMFER_{bevel_type}"

    # Создаем слой, если его ещё нет
    try:
        if layer_name not in [l.dxf.name for l in msp.doc.layers]:
            msp.doc.layers.new(layer_name, dxfattribs={"color": color})
            logger.info(f"Создан новый слой: {layer_name}")
    except Exception as e:
        logger.error(f"Не удалось создать слой {layer_name}: {str(e)}")
        layer_name = "0"

    # Добавляем фаски
    try:
        if offset > 0:  # Если offset положительный, фаска рисуется за пределами детали
            if f_long > 0:
                msp.add_line((x - offset, y - offset), (x + length + offset, y - offset),
                             dxfattribs={"layer": layer_name})
                msp.add_line((x - offset, y + width + offset), (x + length + offset, y + width + offset),
                             dxfattribs={"layer": layer_name})
            if f_short > 0:
                msp.add_line((x - offset, y - offset), (x - offset, y + width + offset),
                             dxfattribs={"layer": layer_name})
                msp.add_line((x + length + offset, y - offset), (x + length + offset, y + width + offset),
                             dxfattribs={"layer": layer_name})
        else:  # Если offset отрицательный, фаска рисуется внутри детали
            if f_long > 0:
                msp.add_line((x - offset, y - offset), (x + length + offset, y - offset),
                             dxfattribs={"layer": layer_name})
                msp.add_line((x - offset, y + width + offset), (x + length + offset, y + width + offset),
                             dxfattribs={"layer": layer_name})
            if f_short > 0:
                msp.add_line((x - offset, y - offset), (x - offset, y + width + offset),
                             dxfattribs={"layer": layer_name})
                msp.add_line((x + length + offset, y - offset), (x + length + offset, y + width + offset),
                             dxfattribs={"layer": layer_name})
    except Exception as e:
        logger.error(f"Ошибка при добавлении линий фаски: {str(e)}")


def add_layout_filename_title(msp, sheet_length, sheet_width, filename):
    """
    Добавляет название файла раскроя над верхним правым углом листа

    Args:
        msp: modelspace DXF документа
        sheet_length: длина листа (мм)
        sheet_width: ширина листа (мм) 
        filename: имя файла раскроя
    """
    try:
        # Получаем только имя файла без пути
        base_filename = os.path.basename(filename)

        # В ezdxf есть два основных способа добавления текста
        # 1. Стандартный add_text
        # 2. add_mtext - позволяет более гибко управлять выравниванием

        # Попробуем сначала mtext, так как он лучше поддерживает выравнивание
        try:
            text_entity = msp.add_mtext(base_filename)
            text_entity.dxf.layer = 'TITLE'
            text_entity.dxf.color = 2  # Желтый
            text_entity.dxf.char_height = 70  # Высота текста

            # Устанавливаем точку вставки по новым координатам
            # Подпись над координатами
            text_entity.dxf.insert = (2800, 2090 + 70)

            # Настраиваем выравнивание (нижний правый угол)
            text_entity.dxf.attachment_point = 6  # 6 = нижний правый угол

            logger.info(
                f"Добавлен заголовок (mtext) с именем файла: {base_filename}")

        except Exception as e:
            # Если mtext не поддерживается, используем обычный текст
            logger.warning(
                f"Не удалось добавить mtext, используем обычный текст: {str(e)}")

            # Добавляем обычный текст с указанием точки привязки
            text_entity = msp.add_text(base_filename)
            text_entity.dxf.layer = 'TITLE'
            text_entity.dxf.color = 2  # Желтый
            text_entity.dxf.height = 70

            # Явно устанавливаем координаты (подпись над точкой)
            text_entity.dxf.insert = (2800, 2090 + 70)

            # Пробуем установить выравнивание разными способами
            try:
                # Используем явные атрибуты выравнивания
                text_entity.dxf.halign = 2  # По правому краю
                text_entity.dxf.valign = 3  # По верху
            except:
                # Если не поддерживается, используем метод set_pos
                try:
                    text_entity.set_pos(
                        (sheet_length, sheet_width),
                        align='TOP_RIGHT'
                    )
                except:
                    # Если и это не работает, делаем приближение вручную
                    # Оценим длину текста (примерно 40 пикселей на символ при высоте 60)
                    text_width = len(base_filename) * 40
                    text_entity.dxf.insert = (
                        sheet_length - text_width, sheet_width)

            logger.info(
                f"Добавлен заголовок (text) с именем файла: {base_filename}")

    except Exception as e:
        logger.error(f"Ошибка при добавлении заголовка: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def add_details_list(msp, sheet_width, details_list, filename=None):
    """
    Добавляет список деталей под картой раскроя в левом нижнем углу.
    Также добавляет имя файла как первый пункт списка с увеличенной высотой.

    Args:
        msp: modelspace DXF документа
        sheet_width: ширина листа (мм)
        details_list: список деталей [(part_id, order_id, size), ...]
        filename: имя файла раскроя (добавляется как первый пункт)
    """
    try:
        # Высота строки и отступ (40 + 40 = 80)
        line_height = 80
        start_y = 0  # Начинаем от нулевой координаты
        line_index = 0  # Индекс строки

        # Добавляем имя файла как первый пункт с увеличенной высотой
        if filename:
            base_filename = os.path.basename(filename)

            # Создаем текст для имени файла
            file_text = msp.add_text(base_filename)
            file_text.dxf.layer = 'PARTSLIST'
            file_text.dxf.color = 2  # Желтый
            file_text.dxf.height = 40  # Высота текста

            # Устанавливаем положение с учетом высоты строки
            file_text.dxf.insert = (0, -line_height * (line_index + 1))

            line_index += 2  # Оставляем дополнительное пространство после имени файла

            logger.info(f"Добавлено имя файла в список: {base_filename}")

        # Сортируем список деталей по part_id
        if details_list:
            # Сортировка по возрастанию part_id (преобразуем в int для правильного порядка)
            sorted_details = sorted(
                details_list, key=lambda x: int(x[0]) if x and x[0] else 0)

            # Добавляем каждую деталь отдельной строкой
            for i, detail_info in enumerate(sorted_details):
                if not detail_info or len(detail_info) < 3:
                    continue

                part_id, order_id, size = detail_info
                # Формируем текст по указанному формату
                text = f"part_{part_id}_{order_id}_{size}"

                # Создаем текст
                text_entity = msp.add_text(text)
                text_entity.dxf.layer = 'PARTSLIST'
                text_entity.dxf.color = 3  # Зеленый
                text_entity.dxf.height = 40

                # Устанавливаем положение с учетом высоты строки
                text_entity.dxf.insert = (
                    0, -line_height * (line_index + i + 1))

                logger.info(f"Добавлена запись в список деталей: {text}")

    except Exception as e:
        logger.error(f"Ошибка при добавлении списка деталей: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def create_new_dxf():
    """
    Создает новый DXF документ с настроенными слоями

    Returns:
        tuple: (doc, msp) - DXF документ и modelspace
    """
    doc = new()
    msp = doc.modelspace()

    # Базовые слои для фасок (с проверкой существования)
    if "CHAMFER_D" not in doc.layers:
        doc.layers.new("CHAMFER_D", dxfattribs={"color": 1})
    if "CHAMFER_C" not in doc.layers:
        doc.layers.new("CHAMFER_C", dxfattribs={"color": 2})

    # Слои для различных типов фасок
    for chamfer_type, props in CHAMFER_TYPES.items():
        layer_name = f"CHAMFER_{chamfer_type}"
        if layer_name not in doc.layers:
            doc.layers.new(layer_name, dxfattribs={"color": props["color"]})

    # Стандартные слои
    doc.layers.new("dimensions", dxfattribs={"color": 7})
    doc.layers.new("TEXT", dxfattribs={"color": 1})
    doc.layers.new("details", dxfattribs={"color": 7})
    doc.layers.new("work_area", dxfattribs={"color": 40})
    doc.layers.new("cut", dxfattribs={"color": 3, "linetype": "CONTINUOUS"})

    # Слои для подписей
    doc.layers.new("TITLE", dxfattribs={"color": 2})
    doc.layers.new("PARTSLIST", dxfattribs={"color": 3})

    # Текстовые стили
    try:
        doc.styles.new('normal_text', dxfattribs={'height': 40})
        doc.styles.new('large_text', dxfattribs={'height': 60})
    except Exception as e:
        logger.warning(f"Не удалось создать текстовый стиль: {str(e)}")

    return doc, msp


def add_detail_dimensions(msp, x, y, width, height, part_id, order_id, thickness):
    """
    Добавляет размеры и метки на чертеж внутри детали в нижнем левом углу.
    Текст расположен вдоль длинной стороны и поворачивается вместе с деталью.

    Args:
        msp: modelspace DXF документа
        x, y: начальные координаты левого нижнего угла детали
        width, height: размеры детали
        part_id: ID детали
        order_id: ID заказа
        thickness: толщина материала
    """
    # Гарантируем, что параметры преобразованы в строки для безопасного отображения
    part_id = str(part_id) if part_id is not None else "?"
    order_id = str(order_id) if order_id is not None else "?"
    thickness = str(thickness) if thickness is not None else "?"

    # Формируем текст подписи: номер детали, номер заказа, размер
    text = f"{part_id} {order_id} {width}x{height}"

    # Отступ от края детали для размещения текста
    margin = 5

    # Определяем ориентацию детали
    is_vertical = height > width

    try:
        # Создаем текст с соответствующими атрибутами
        text_entity = msp.add_text(text)
        text_entity.dxf.layer = 'TEXT'
        text_entity.dxf.color = 1  # Красный
        text_entity.dxf.height = 40

        # Устанавливаем положение и поворот в зависимости от ориентации детали
        if is_vertical:
            # Для вертикальной детали - поворот на 90° и размещение в правом нижнем углу
            text_entity.dxf.insert = (x + width - margin, y + margin)
            text_entity.dxf.rotation = 90
        else:
            # Для горизонтальной детали - без поворота, в левом нижнем углу
            text_entity.dxf.insert = (x + margin, y + margin)
            text_entity.dxf.rotation = 0
    except Exception as e:
        logger.error(f"Ошибка при добавлении текста: {str(e)}")


def add_sheet_outline(msp, sheet_length, sheet_width, margin):
    """
    Добавляет контур листа и границу рабочей области на чертеж

    Args:
        msp: modelspace DXF документа
        sheet_length, sheet_width: полные размеры листа
        margin: отступ от края листа до рабочей области (мм)
    """
    try:
        # Полный контур листа
        msp.add_lwpolyline([
            (0, 0),
            (sheet_length, 0),
            (sheet_length, sheet_width),
            (0, sheet_width),
            (0, 0)
        ], dxfattribs={'layer': '0'})

        # Граница рабочей области (с отступом margin от края)
        msp.add_lwpolyline([
            (margin, margin),
            (sheet_length - margin, margin),
            (sheet_length - margin, sheet_width - margin),
            (margin, sheet_width - margin),
            (margin, margin)
        ], dxfattribs={'layer': 'work_area'})
    except Exception as e:
        logger.error(f"Ошибка при добавлении контуров: {str(e)}")


def add_cut_line(msp, x, y, width, height, offset):
    """
    Добавляет линию реза со смещением от контура детали

    Args:
        msp: modelspace DXF документа
        x, y: координаты левого нижнего угла детали
        width, height: размеры детали
        offset: смещение линии реза от контура (мм)
    """
    try:
        # Добавляем контур реза со смещением
        msp.add_lwpolyline([
            (x - offset, y - offset),
            (x + width + offset, y - offset),
            (x + width + offset, y + height + offset),
            (x - offset, y + height + offset),
            (x - offset, y - offset)
        ], dxfattribs={'layer': 'cut', 'color': 3})
    except Exception as e:
        logger.error(f"Ошибка при добавлении линии реза: {str(e)}")


def add_detail_to_sheet(msp, detail, rect_info, kerf):
    """
    Добавляет деталь на лист

    Args:
        msp: modelspace DXF документа
        detail: данные детали (DataFrame row)
        rect_info: информация о расположении детали на листе {'x', 'y', 'width', 'height', 'rotated'}
        kerf: диаметр фрезы, создающий отступ между деталями (мм)

    Returns:
        tuple: (part_id, order_id, size_str) - информация о детали для списка деталей
    """
    try:
        logger.info(f"Добавление детали: {detail['part_id']}")
        part_id = str(detail['part_id'])

        # Оригинальные размеры детали из таблицы
        orig_width = detail['length_mm']
        orig_height = detail['width_mm']

        # Координаты левого нижнего угла детали
        detail_x = rect_info['x']
        detail_y = rect_info['y']

        # Проверяем, есть ли прямое указание о повороте детали
        is_rotated = rect_info.get('rotated', False)

        logger.info(f"Деталь {part_id}: is_rotated={is_rotated}, " +
                    f"оригинальные размеры: {orig_width}x{orig_height}")

        # Размеры детали для отрисовки
        if is_rotated:
            # Деталь повернута - меняем ширину и высоту местами
            detail_width = orig_height
            detail_height = orig_width
            logger.info(
                f"Деталь {part_id} повернута, отрисовка с размерами: {detail_width}x{detail_height}")
        else:
            # Деталь не повернута - используем оригинальные размеры
            detail_width = orig_width
            detail_height = orig_height
            logger.info(
                f"Деталь {part_id} не повернута, отрисовка с размерами: {detail_width}x{detail_height}")

        # Добавляем контур детали
        msp.add_lwpolyline([
            (detail_x, detail_y),
            (detail_x + detail_width, detail_y),
            (detail_x + detail_width, detail_y + detail_height),
            (detail_x, detail_y + detail_height),
            (detail_x, detail_y)
        ], dxfattribs={'layer': 'details'})

        # Добавляем линию реза со смещением 2мм (половина kerf)
        add_cut_line(msp, detail_x, detail_y,
                     detail_width, detail_height, kerf/2)

        # Добавляем фаски, если нужно
        # Гарантируем, что тип фаски - строка
        bevel_type = str(detail.get('bevel_type', '')) if detail.get(
            'bevel_type') is not None else ''

        # Получаем смещение фаски из таблицы, если оно указано
        bevel_offset = None
        if 'bevel_offset_mm' in detail and detail['bevel_offset_mm'] is not None:
            try:
                bevel_offset = float(detail['bevel_offset_mm'])
                logger.info(
                    f"Используется смещение фаски из таблицы: {bevel_offset}")
            except (ValueError, TypeError):
                logger.warning(
                    f"Некорректное значение смещения фаски: {detail['bevel_offset_mm']}")

        # Получаем значения фасок - сначала проверяем новые имена колонок, затем старые
        if 'f_long' in detail:
            f_long = int(detail.get('f_long', 0)) if detail.get(
                'f_long') is not None else 0
        elif 'f_длина' in detail:
            f_long = int(detail.get('f_длина', 0)) if detail.get(
                'f_длина') is not None else 0
        else:
            f_long = 0

        if 'f_short' in detail:
            f_short = int(detail.get('f_short', 0)) if detail.get(
                'f_short') is not None else 0
        elif 'f_ширина' in detail:
            f_short = int(detail.get('f_ширина', 0)) if detail.get(
                'f_ширина') is not None else 0
        else:
            f_short = 0

        if bevel_type and bevel_type.lower() not in ['нет', 'none', 'no']:
            # Применяем фаски в зависимости от положения детали
            if is_rotated:
                # Если деталь повернута, меняем параметры фасок местами
                add_bevels(msp, detail_x, detail_y, detail_width, detail_height,
                           bevel_type, f_short, f_long, bevel_offset)
            else:
                add_bevels(msp, detail_x, detail_y, detail_width, detail_height,
                           bevel_type, f_long, f_short, bevel_offset)

        # Добавляем размеры и метки
        logger.info(
            f"Добавление текста для детали {part_id}, координаты: {detail_x}, {detail_y}")
        order_id = detail.get('order_id', None)
        thickness = detail.get('thickness_mm', None)
        material = detail.get('material', 'S')

        # Форматируем толщину с материалом для отображения
        thickness_display = f"{thickness}{material}" if material and material != 'S' else str(
            thickness)

        add_detail_dimensions(msp, detail_x, detail_y, detail_width, detail_height,
                              part_id, order_id, thickness_display)

        # Возвращаем информацию о детали для последующего использования в списке деталей
        size_str = f"{orig_width}x{orig_height}"
        return part_id, order_id, size_str

    except Exception as e:
        logger.error(
            f"Ошибка при добавлении детали {detail.get('part_id', 'unknown')}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# Заглушка для работы с узорами - просто заглушка, не выполняет никаких действий
def load_patterns(pattern_dir):
    """
    Заглушка для загрузки узоров. В текущей версии не используется.

    Args:
        pattern_dir: директория с узорами

    Returns:
        dict: пустой словарь
    """
    logger.info(
        f"Папка с узорами: {pattern_dir} (функциональность узоров отключена)")
    return {}
