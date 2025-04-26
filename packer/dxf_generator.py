import ezdxf
from ezdxf.filemanagement import new
import re
import os.path
from .config import logger


def normalize_layer_name(name):
    """
    Очищает имя слоя от недопустимых символов, сохраняя максимум исходных символов.

    В DXF имена слоев не могут содержать некоторые специальные символы.
    Эта функция заменяет только безусловно недопустимые символы, стараясь 
    максимально сохранить исходное имя.

    Args:
        name: исходное имя слоя

    Returns:
        str: очищенное имя слоя, безопасное для использования в DXF
    """
    if not name:
        return "UNNAMED"

    # Заменяем только безусловно недопустимые для DXF символы
    # Сохраняем больше символов, включая не-ASCII символы, если это возможно
    safe_name = ""
    for char in name:
        # Разрешаем буквы, цифры, подчеркивания, дефисы, точки, доллары
        if char.isalnum() or char in '_-.$ ':
            safe_name += char
        else:
            # Для других символов используем подчеркивание
            safe_name += '_'

    # Проверяем, что имя не пустое после очистки
    if not safe_name or safe_name.isspace():
        return "UNNAMED"

    # Убираем начальные и конечные пробелы
    safe_name = safe_name.strip()

    # Логируем информацию, если имя было изменено
    if safe_name != name:
        from .config import logger
        logger.info(f"Имя слоя нормализовано: '{name}' -> '{safe_name}'")

    return safe_name


def add_bevel_lines(msp, x, y, length, width, bevel_type, f_long=0, f_short=0, bevel_offset=None, is_rotated=False):
    """
    Добавляет линии фасок на деталь с расширенной логикой удлинения линий для создания замкнутых контуров.

    При положительном смещении фаски и наличии фасок с нескольких сторон,
    линии фасок удлиняются для образования замкнутого контура.

    Args:
        msp: modelspace DXF документа
        x, y: координаты левого нижнего угла детали
        length, width: размеры детали
        bevel_type: тип фаски
        f_long: значения фасок по длине (длинная сторона) (0 - нет, 1 - с одной стороны, 2 - с обеих)
        f_short: значения фасок по ширине (короткая сторона) (0 - нет, 1 - с одной стороны, 2 - с обеих)
        bevel_offset: смещение фаски (мм), положительное - наружу, отрицательное - внутрь
        is_rotated: флаг, указывающий, повернута ли деталь на 90 градусов 
    """
    if not bevel_type or bevel_type.lower() in ['нет', 'none', 'no']:
        return

    # Определяем смещение фаски
    if bevel_offset is None:
        offset = 0
        logger.warning(
            f"Смещение фаски не указано для {bevel_type}, используется {offset}")
    else:
        offset = bevel_offset
        logger.info(f"Используется смещение фаски из таблицы: {offset}")

    # Работаем с исходным типом фаски, сохраняя кириллицу
    original_layer_name = bevel_type

    # Создаем безопасное имя слоя, которое будет работать в DXF
    safe_layer_name = ''
    for char in original_layer_name:
        if ord(char) == 0xFFFD:
            safe_layer_name += '_'
        elif char.isalnum() or char.isalpha() or char in '_-./$':
            safe_layer_name += char
        else:
            safe_layer_name += '_'

    if not safe_layer_name or safe_layer_name.isspace():
        safe_layer_name = "BEVEL_TYPE"

    # Создаем слой
    layer_name = safe_layer_name

    try:
        existing_layers = [l.dxf.name for l in msp.doc.layers]
        if layer_name not in existing_layers:
            msp.doc.layers.new(layer_name, dxfattribs={"color": 1})
            logger.info(f"Создан новый слой фаски: {layer_name}")
    except Exception as e:
        logger.error(f"Не удалось создать слой фаски '{layer_name}': {str(e)}")
        try:
            translit_layer_name = "BEVEL_" + \
                ''.join([c if ord(c) < 128 else '_' for c in original_layer_name])
            if translit_layer_name not in existing_layers:
                msp.doc.layers.new(translit_layer_name,
                                   dxfattribs={"color": 1})
            layer_name = translit_layer_name
            logger.info(f"Создан транслитерированный слой фаски: {layer_name}")
        except Exception as e2:
            logger.error(
                f"Не удалось создать транслитерированный слой: {str(e2)}")
            try:
                fallback_layer = "BEVEL"
                if fallback_layer not in existing_layers:
                    msp.doc.layers.new(fallback_layer, dxfattribs={"color": 1})
                layer_name = fallback_layer
                logger.info(
                    f"Используем запасной слой для фаски: {layer_name}")
            except Exception as e3:
                logger.error(f"Не удалось создать запасной слой: {str(e3)}")
                layer_name = "0"

    layer_attributes = {"layer": layer_name, "color": 1}

    try:
        # Определяем, нужно ли удлинять линии фаски
        # Удлинение нужно только если смещение фаски положительное и не равно нулю
        extend_bevels = offset > 0

        # Переменные удлинения для каждой линии
        left_extend_top = 0
        left_extend_bottom = 0
        right_extend_top = 0
        right_extend_bottom = 0
        bottom_extend_left = 0
        bottom_extend_right = 0
        top_extend_left = 0
        top_extend_right = 0

        # Рассчитываем удлинения для различных комбинаций фасок
        if extend_bevels:
            # Случай 1: фаска по всему периметру (2,2)
            if f_long == 2 and f_short == 2:
                left_extend_top = offset
                left_extend_bottom = offset
                right_extend_top = offset
                right_extend_bottom = offset
                bottom_extend_left = offset
                bottom_extend_right = offset
                top_extend_left = offset
                top_extend_right = offset
            # Случай 2: фаска только по длине (2,0) или только по ширине (0,2)
            # Удлинение не требуется, оставляем значения по умолчанию (0)

            # Случай 3: фаска по длине с двух сторон и по ширине с одной (2,1)
            elif f_long == 2 and f_short == 1:
                if is_rotated:
                    # Удлиняем нижнюю горизонтальную линию с обоих концов
                    bottom_extend_left = offset
                    bottom_extend_right = offset
                    # Удлиняем вертикальные линии только снизу
                    left_extend_bottom = offset
                    right_extend_bottom = offset
                else:
                    # Удлиняем левую вертикальную линию с обоих концов
                    left_extend_top = offset
                    left_extend_bottom = offset
                    # Удлиняем горизонтальные линии только слева
                    bottom_extend_left = offset
                    top_extend_left = offset

            # Случай 4: фаска по длине с одной стороны и по ширине с двух (1,2)
            elif f_long == 1 and f_short == 2:
                if is_rotated:
                    # Удлиняем левую вертикальную линию с обоих концов
                    left_extend_top = offset
                    left_extend_bottom = offset
                    # Удлиняем горизонтальные линии только слева
                    bottom_extend_left = offset
                    top_extend_left = offset
                else:
                    # Удлиняем нижнюю горизонтальную линию с обоих концов
                    bottom_extend_left = offset
                    bottom_extend_right = offset
                    # Удлиняем вертикальные линии только снизу
                    left_extend_bottom = offset
                    right_extend_bottom = offset

            # Случай 5: фаска по длине с одной стороны и по ширине с одной (1,1) - "буква Г"
            elif f_long == 1 and f_short == 1:
                # Удлиняем линии только в месте пересечения
                if is_rotated:
                    # Для повернутой детали это левая вертикальная и нижняя горизонтальная
                    left_extend_bottom = offset
                    bottom_extend_left = offset
                else:
                    # Для стандартной ориентации это нижняя горизонтальная и левая вертикальная
                    bottom_extend_left = offset
                    left_extend_bottom = offset

        # Особый случай - фаска со всех четырех сторон (f_long=2 и f_short=2)
        # Отрисовываем замкнутой полилинией
        if f_long == 2 and f_short == 2 and offset > 0:
            # Создаем замкнутую полилинию для фаски по всему периметру
            points = [
                (x - offset, y - offset),                   # Левый нижний угол
                (x + length + offset, y - offset),          # Правый нижний угол
                (x + length + offset, y + width + offset),  # Правый верхний угол
                (x - offset, y + width + offset),           # Левый верхний угол
                (x - offset, y - offset)                    # Замыкаем контур
            ]

            msp.add_lwpolyline(points, dxfattribs=layer_attributes)
            logger.info(
                f"Добавлена замкнутая полилиния фаски по всему периметру")
            return  # Выходим из функции, так как фаска уже нарисована

        if is_rotated:
            # Поворот на 90 градусов: длина соответствует высоте, ширина — ширине
            # Фаски по длине (f_long) — на вертикальных сторонах
            if f_long > 0:
                # Левая вертикальная линия (смещение по X влево для положительного offset)
                msp.add_line(
                    (x - offset, y - left_extend_bottom),
                    (x - offset, y + width + left_extend_top),
                    dxfattribs=layer_attributes
                )
                if f_long >= 2:
                    # Правая вертикальная линия (смещение по X вправо)
                    msp.add_line(
                        (x + length + offset, y - right_extend_bottom),
                        (x + length + offset, y + width + right_extend_top),
                        dxfattribs=layer_attributes
                    )

            # Фаски по ширине (f_short) — на горизонтальных сторонах
            if f_short > 0:
                # Нижняя горизонтальная линия (смещение по Y вниз)
                msp.add_line(
                    (x - bottom_extend_left, y - offset),
                    (x + length + bottom_extend_right, y - offset),
                    dxfattribs=layer_attributes
                )
                if f_short >= 2:
                    # Верхняя горизонтальная линия (смещение по Y вверх)
                    msp.add_line(
                        (x - top_extend_left, y + width + offset),
                        (x + length + top_extend_right, y + width + offset),
                        dxfattribs=layer_attributes
                    )
        else:
            # Без поворота: длина — горизонтальная, ширина — вертикальная
            # Фаски по длине (f_long) — на горизонтальных сторонах
            if f_long > 0:
                # Нижняя горизонтальная линия (смещение по Y вниз)
                msp.add_line(
                    (x - bottom_extend_left, y - offset),
                    (x + length + bottom_extend_right, y - offset),
                    dxfattribs=layer_attributes
                )
                if f_long >= 2:
                    # Верхняя горизонтальная линия (смещение по Y вверх)
                    msp.add_line(
                        (x - top_extend_left, y + width + offset),
                        (x + length + top_extend_right, y + width + offset),
                        dxfattribs=layer_attributes
                    )

            # Фаски по ширине (f_short) — на вертикальных сторонах
            if f_short > 0:
                # Левая вертикальная линия (смещение по X влево)
                msp.add_line(
                    (x - offset, y - left_extend_bottom),
                    (x - offset, y + width + left_extend_top),
                    dxfattribs=layer_attributes
                )
                if f_short >= 2:
                    # Правая вертикальная линия (смещение по X вправо)
                    msp.add_line(
                        (x + length + offset, y - right_extend_bottom),
                        (x + length + offset, y + width + right_extend_top),
                        dxfattribs=layer_attributes
                    )

    except Exception as e:
        logger.error(f"Ошибка при добавлении фасок: {str(e)}")


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
        orig_length = detail['length_mm']  # Длина (всегда большая сторона)
        orig_width = detail['width_mm']    # Ширина (всегда меньшая сторона)

        # Координаты левого нижнего угла детали
        detail_x = rect_info['x']
        detail_y = rect_info['y']

        # Проверяем, есть ли прямое указание о повороте детали
        is_rotated = rect_info.get('rotated', False)

        logger.info(f"Деталь {part_id}: is_rotated={is_rotated}, " +
                    f"оригинальные размеры: {orig_length}x{orig_width}")

        # Размеры детали для отрисовки
        if is_rotated:
            # Деталь повернута - меняем ширину и высоту местами
            detail_width = orig_width
            detail_height = orig_length
            logger.info(
                f"Деталь {part_id} повернута, отрисовка с размерами: {detail_width}x{detail_height}")
        else:
            # Деталь не повернута - используем оригинальные размеры
            detail_width = orig_length
            detail_height = orig_width
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

        # Получаем значения фасок по длине и ширине
        f_long = int(detail.get('f_long', 0)) if detail.get(
            'f_long') is not None else 0
        f_short = int(detail.get('f_short', 0)) if detail.get(
            'f_short') is not None else 0

        if bevel_type and bevel_type.lower() not in ['нет', 'none', 'no']:
            # Добавляем фаски с учетом поворота детали
            add_bevel_lines(msp, detail_x, detail_y, detail_width, detail_height,
                            bevel_type, f_long, f_short, bevel_offset, is_rotated)

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
        size_str = f"{orig_length}x{orig_width}"
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
