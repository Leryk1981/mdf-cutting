import os
from rectpack import newPacker, MaxRectsBssf
from .config import logger
from .patterns import load_patterns
from .dxf_generator import (
    create_new_dxf,
    add_sheet_outline,
    add_detail_to_sheet,
    add_layout_filename_title,
    add_details_list
)
from .remnants import RemnantsManager
from .file_organizer import get_organized_file_path
from .constants import (
    MATERIALS_REQUIRED_COLUMNS,
    DETAILS_REQUIRED_COLUMNS,
    DEFAULT_MARGIN,
    DEFAULT_KERF
)


def hybrid_sort(rectangles):
    """Сортировка деталей для HybridMaxRects - сначала большие, потом средние, потом мелкие."""
    large, medium, small = [], [], []
    for w, h, idx in rectangles:
        if w > 2000:
            large.append((w, h, idx))
        elif w < 800:
            small.append((w, h, idx))
        else:
            medium.append((w, h, idx))
    return (sorted(large, key=lambda x: -(x[0] * x[1])) +
            sorted(medium, key=lambda x: -(x[0] * x[1])) +
            sorted(small, key=lambda x: (-x[0], -x[1])))


def format_remnant_id(remnant_id):
    """
    Форматирует ID остатка для отображения в имени файла.
    Убирает десятичную точку и нули у числовых ID.

    Args:
        remnant_id: ID остатка из таблицы

    Returns:
        Форматированный ID остатка для имени файла
    """
    # Проверка на None
    if remnant_id is None:
        return "unknown"

    # Преобразуем в строку, если ещё не строка
    if not isinstance(remnant_id, str):
        # Если это число с десятичной точкой (например 14.0)
        if isinstance(remnant_id, float) and remnant_id.is_integer():
            # Преобразуем в целое число и затем в строку (14.0 -> 14)
            return str(int(remnant_id))
        return str(remnant_id)

    # Для строковых значений, пробуем преобразовать к целому числу, если это число с точкой
    try:
        if '.' in remnant_id:
            float_val = float(remnant_id)
            if float_val.is_integer():
                return str(int(float_val))
    except (ValueError, TypeError):
        pass

    return remnant_id


def pack_and_generate_dxf(details_df, materials_df, pattern_dir="patterns", margin=DEFAULT_MARGIN, kerf=DEFAULT_KERF):
    """
    Упаковывает детали и генерирует DXF файлы с приоритетом остатков.
    Гарантирует сохранение оригинальных remnant_id при создании карт раскроя.

    Args:
        details_df: DataFrame с деталями
        materials_df: DataFrame с материалами
        pattern_dir: директория с узорами
        margin: отступ от края листа (мм)
        kerf: диаметр фрезы (мм)

    Returns:
        tuple: (словарь упаковщиков, количество использованных листов, количество карт раскроя)
    """
    # Импортируем нужные алгоритмы из rectpack
    from rectpack import MaxRectsBaf, MaxRectsBssf

    print("Запуск упаковки с полным приоритетом остатков")
    logger.info("Запуск упаковки с полным приоритетом остатков")

    packers_by_material = {}
    total_used_sheets = 0
    remnants_manager = RemnantsManager(margin=margin, kerf=kerf)
    current_materials_df = materials_df.copy()
    layout_count = 0  # Подсчёт созданных карт раскроя

    # Проверка наличия обязательных колонок
    for col in MATERIALS_REQUIRED_COLUMNS:
        if col not in current_materials_df.columns:
            logger.error(f"Отсутствует колонка '{col}' в materials_df")
            raise ValueError(f"Missing column '{col}' in materials_df")
    for col in DETAILS_REQUIRED_COLUMNS:
        if col not in details_df.columns:
            logger.error(f"Отсутствует колонка '{col}' в details_df")
            raise ValueError(f"Missing column '{col}' in details_df")

    # Добавляем колонку remnant_id, если её нет в таблице материалов
    if 'remnant_id' not in current_materials_df.columns:
        current_materials_df['remnant_id'] = None
        logger.info(
            "Добавлена колонка 'remnant_id' со значением None для исходной таблицы материалов")

    unique_combinations = details_df[[
        'thickness_mm', 'material']].drop_duplicates()
    logger.info(
        f"Найдено {len(unique_combinations)} комбинаций материалов/толщин")

    for _, row in unique_combinations.iterrows():
        thickness = row['thickness_mm']
        material = row['material']
        material_key = thickness if material == 'S' else f"{thickness}_{material}"
        logger.info(
            f"\nОбработка: толщина={thickness}, материал={material}, ключ={material_key}")

        # Выбираем детали для текущей комбинации материал/толщина
        detail_mask = (details_df['thickness_mm'] == thickness) & (
            details_df['material'] == material)
        material_details = details_df[detail_mask].copy()
        if material_details.empty:
            logger.info("Нет деталей для этой комбинации")
            continue

        # Выбираем листы материала для текущей комбинации
        material_mask = (current_materials_df['thickness_mm'] == thickness) & (
            current_materials_df['material'] == material)
        material_sheets = current_materials_df[material_mask].copy()
        if material_sheets.empty:
            logger.info("Нет листов материала для этой комбинации")
            continue

        # Подготовка деталей для упаковки
        rects_to_pack = []
        # Создаем счетчик для уникальных идентификаторов копий деталей
        unique_id_counter = 0
        material_details = material_details.reset_index(drop=True)

        for idx, detail in material_details.iterrows():
            packing_width = detail['length_mm'] + kerf
            packing_height = detail['width_mm'] + kerf
            if packing_width <= 0 or packing_height <= 0:
                logger.info(
                    f"Пропуск детали {detail['part_id']}: некорректные размеры {packing_width}x{packing_height}")
                continue

            quantity = max(1, int(detail.get('quantity', 1)))

            # Логируем информацию о детали для отладки
            logger.info(f"Обработка детали ID={detail['part_id']}, " +
                        f"размеры={detail['length_mm']}x{detail['width_mm']}, " +
                        f"количество={quantity}")

            # Добавляем каждую копию детали с уникальным ID
            for q in range(quantity):
                # Создаем уникальный ID для каждой копии: tuple(idx, unique_id)
                unique_id = (idx, unique_id_counter)
                unique_id_counter += 1
                rects_to_pack.append(
                    (packing_width, packing_height, unique_id))

                logger.info(f"Добавлена копия {q+1}/{quantity} детали {detail['part_id']} " +
                            f"с уникальным ID={unique_id}")

        if not rects_to_pack:
            logger.info("Нет деталей для упаковки")
            continue

        logger.info(f"Подготовлено {len(rects_to_pack)} деталей для упаковки")

        # Подготовка остатков
        remnants = []
        remnant_sheets = material_sheets[material_sheets['is_remnant'] == True].copy(
        )
        logger.info(f"Найдено {len(remnant_sheets)} типов остатков")

        # Создаем словарь для просмотра остатков по их ID
        remnant_by_id = {}

        # Добавляем остатки в список
        for _, row in remnant_sheets.iterrows():
            # Получаем remnant_id - ключевое значение
            remnant_id = row.get('remnant_id', None)
            if remnant_id is None:
                logger.warning(f"Пропуск остатка без ID: {row}")
                continue

            remnant_length = float(row['sheet_length_mm'])
            remnant_width = float(row['sheet_width_mm'])

            # Проверяем размеры
            if remnant_length <= 0 or remnant_width <= 0:
                logger.warning(
                    f"Пропуск остатка с ID={remnant_id} с некорректными размерами: {remnant_length}x{remnant_width}")
                continue

            # Добавляем каждый экземпляр остатка
            for _ in range(int(row['total_quantity'])):
                remnant = {
                    'width': remnant_width,
                    'length': remnant_length,
                    'remnant_id': remnant_id,
                    'width_with_margin': remnant_width - 2 * margin,
                    'length_with_margin': remnant_length - 2 * margin
                }
                remnants.append(remnant)

                # Сохраняем для быстрого доступа
                remnant_by_id[remnant_id] = remnant

            logger.info(
                f"Добавлен остаток с ID={remnant_id}, размеры={remnant_length}x{remnant_width}")

        logger.info(f"Подготовлено {len(remnants)} остатков")

        # Сортируем остатки по убыванию площади
        if remnants:
            remnants.sort(key=lambda x: x['width'] * x['length'], reverse=True)
            logger.info("Остатки отсортированы по площади (убывание)")

        # Подготовка целых листов
        full_sheets = []
        full_sheet_rows = material_sheets[material_sheets['is_remnant'] == False]

        for _, row in full_sheet_rows.iterrows():
            sheet_length = float(row['sheet_length_mm'])
            sheet_width = float(row['sheet_width_mm'])

            # Проверяем размеры
            if sheet_length <= 0 or sheet_width <= 0:
                logger.warning(
                    f"Пропуск листа с некорректными размерами: {sheet_length}x{sheet_width}")
                continue

            # Добавляем каждый экземпляр листа
            for _ in range(int(row['total_quantity'])):
                full_sheets.append({
                    'width': sheet_width,
                    'length': sheet_length,
                    'width_with_margin': sheet_width - 2 * margin,
                    'length_with_margin': sheet_length - 2 * margin
                })

        logger.info(f"Подготовлено {len(full_sheets)} целых листов")

        if not remnants and not full_sheets:
            logger.info("Нет контейнеров для упаковки")
            continue

        # Сортируем детали для более эффективной упаковки
        rects_to_pack = hybrid_sort(rects_to_pack)

        # Подготовка упаковщиков
        # Список упаковщиков (container_type, container_id, packer)
        all_packers = []
        used_remnant_ids = set()  # Набор использованных remnant_id
        used_full_sheets = 0  # Счетчик использованных целых листов

        # ФАЗА 1: Упаковка в остатки
        logger.info("\nФаза 1: Упаковка в остатки")

        for remnant in remnants:
            remnant_id = remnant['remnant_id']

            # Создаем отдельный упаковщик для каждого остатка
            logger.info(f"Создание упаковщика для остатка с ID={remnant_id}")
            packer = newPacker(rotation=True, pack_algo=MaxRectsBaf)

            # Важно: используем размеры с учетом отступов
            width_with_margin = remnant['width_with_margin']
            length_with_margin = remnant['length_with_margin']

            # Добавляем контейнер с размерами за вычетом отступов
            packer.add_bin(length_with_margin, width_with_margin)

            # Находим неупакованные детали
            remaining_rects = []
            packed_ids = set()  # Множество для хранения уже упакованных деталей

            # Соберем все упакованные детали из всех предыдущих контейнеров
            for p_type, p_id, p in all_packers:
                if len(p) > 0 and p[0]:  # Проверяем наличие контейнера и деталей
                    for rect in p[0]:
                        # rect.rid теперь будет уникальным ID
                        packed_ids.add(rect.rid)

            # Подробно логируем количество найденных упакованных деталей
            logger.info(
                f"Найдено {len(packed_ids)} упакованных деталей из {len(rects_to_pack)} всего")

            # Проверяем каждую деталь из списка подготовленных
            for w, h, unique_id in rects_to_pack:
                if unique_id not in packed_ids:
                    remaining_rects.append((w, h, unique_id))

            logger.info(f"Осталось упаковать {len(remaining_rects)} деталей")

            # Добавляем все неупакованные детали
            for w, h, idx in remaining_rects:
                packer.add_rect(w, h, idx)

            # Выполняем упаковку
            packer.pack()

            # Проверяем, есть ли что-то в упаковщике
            # Пустой контейнер или нет контейнеров
            if len(packer) == 0 or not packer[0]:
                logger.info(
                    f"Остаток с ID={remnant_id} не использован - не удалось упаковать детали")
                continue

            # Если упаковка успешна, сохраняем результат
            logger.info(f"Остаток с ID={remnant_id} успешно использован")
            all_packers.append(("remnant", remnant_id, packer))
            used_remnant_ids.add(remnant_id)

        logger.info(f"Использовано остатков: {len(used_remnant_ids)}")

        # ФАЗА 2: Упаковка оставшихся деталей в целые листы
        logger.info("\nФаза 2: Упаковка в целые листы")

        # Находим все детали, которые уже упакованы
        packed_rects = set()
        for p_type, p_id, packer in all_packers:
            # Проверяем наличие контейнера и деталей
            if len(packer) > 0 and packer[0]:
                # Добавляем уникальные ID в множество упакованных деталей
                for rect in packer[0]:
                    packed_rects.add(rect.rid)

        logger.info(
            f"Перед упаковкой на листы: найдено {len(packed_rects)} упакованных деталей")

        # Определяем неупакованные детали - формируем новый список
        remaining_rects = []
        for w, h, unique_id in rects_to_pack:
            if unique_id not in packed_rects:
                remaining_rects.append((w, h, unique_id))

        logger.info(
            f"Осталось упаковать на листы: {len(remaining_rects)} деталей")

        if remaining_rects and full_sheets:
            logger.info(
                f"Осталось упаковать {len(remaining_rects)} деталей в целые листы")

            # Упаковываем оставшиеся детали в целые листы
            for i, sheet in enumerate(full_sheets):
                if not remaining_rects:
                    break

                # Создаем упаковщик для текущего листа
                packer = newPacker(rotation=True, pack_algo=MaxRectsBssf)

                # Добавляем контейнер с размерами за вычетом отступов
                packer.add_bin(sheet['length_with_margin'],
                               sheet['width_with_margin'])

                # Добавляем все оставшиеся детали
                for w, h, idx in remaining_rects:
                    packer.add_rect(w, h, idx)

                # Выполняем упаковку
                packer.pack()

                # Проверяем, есть ли что-то в упаковщике
                # Пустой контейнер или нет контейнеров
                if len(packer) == 0 or not packer[0]:
                    continue

                # Если упаковка успешна, сохраняем результат
                sheet_id = i  # Просто индекс листа
                all_packers.append(("sheet", sheet_id, packer))
                used_full_sheets += 1

                # Обновляем список упакованных деталей
                newly_packed_ids = set()
                for rect in packer[0]:
                    newly_packed_ids.add(rect.rid)

                # Добавляем в общий список упакованных
                packed_rects.update(newly_packed_ids)

                # Обновляем список оставшихся деталей - важно пересоздать список полностью
                remaining_rects_new = []
                for w, h, unique_id in remaining_rects:
                    if unique_id not in newly_packed_ids:
                        remaining_rects_new.append((w, h, unique_id))

                logger.info(
                    f"Лист {i}: упаковано {len(newly_packed_ids)} деталей, осталось {len(remaining_rects_new)}")
                remaining_rects = remaining_rects_new  # Заменяем список

        logger.info(f"Использовано целых листов: {used_full_sheets}")

        # ФАЗА 3: Создание DXF файлов и финального упаковщика
        logger.info("\nФаза 3: Создание DXF файлов")

        # Создаем финальный упаковщик
        final_packer = newPacker(rotation=True, pack_algo=MaxRectsBssf)
        bin_counter = 0

        # Обрабатываем каждый упаковщик
        for container_type, container_id, packer in all_packers:
            # Пропускаем пустые контейнеры
            if len(packer) == 0 or not packer[0]:
                continue

            # Определяем тип контейнера
            is_remnant = (container_type == "remnant")

            # Получаем информацию о размерах
            if is_remnant:
                # Для остатка
                remnant_id = container_id
                remnant = remnant_by_id.get(remnant_id)
                if not remnant:
                    logger.error(
                        f"Не найдена информация об остатке с ID={remnant_id}")
                    continue

                original_width = remnant['width']
                original_length = remnant['length']
                width_with_margin = remnant['width_with_margin']
                length_with_margin = remnant['length_with_margin']
            else:
                # Для целого листа
                sheet_idx = container_id
                if sheet_idx >= len(full_sheets):
                    logger.error(
                        f"Индекс листа {sheet_idx} выходит за пределы списка листов")
                    continue

                sheet = full_sheets[sheet_idx]
                original_width = sheet['width']
                original_length = sheet['length']
                width_with_margin = sheet['width_with_margin']
                length_with_margin = sheet['length_with_margin']

            # Создаем DXF документ
            try:
                doc, msp = create_new_dxf()
                add_sheet_outline(msp, original_length, original_width, margin)
                details_list = []

                # Добавляем все детали в DXF
                for rect in packer[0]:
                    # Извлекаем индекс детали из rid (теперь это кортеж (idx, unique_id))
                    detail_idx = rect.rid[0] if isinstance(
                        rect.rid, tuple) else rect.rid
                    detail = material_details.iloc[detail_idx]

                    # Рассчитываем фактические размеры детали (за вычетом kerf)
                    rect_width = rect.width - kerf
                    rect_height = rect.height - kerf

                    # Определяем, была ли деталь повернута
                    orig_width = detail['length_mm']
                    orig_height = detail['width_mm']
                    is_rotated = (abs(rect_width - orig_width) >
                                  0.1) or (abs(rect_height - orig_height) > 0.1)

                    # Создаем информацию о детали для DXF
                    detail_rect = {
                        'x': rect.x + margin,
                        'y': rect.y + margin,
                        'width': rect_width,
                        'height': rect_height,
                        'rotated': is_rotated
                    }

                    # Добавляем деталь в DXF
                    detail_info = add_detail_to_sheet(
                        msp, detail, detail_rect, kerf)
                    if detail_info:
                        details_list.append(detail_info)

                    # Выводим информацию о копии детали для отладки
                    copy_id = rect.rid[1] if isinstance(rect.rid, tuple) else 0
                    logger.info(f"Добавлена деталь {detail['part_id']} (копия ID: {copy_id}) " +
                                f"в DXF с размерами {rect_width}x{rect_height}")

                # Формируем имя файла
                if is_remnant:
                    # Для остатка используем original remnant_id
                    # Форматируем ID (убираем .0 в конце для целых значений)
                    formatted_id = format_remnant_id(remnant_id)

                    # Преобразуем thickness в целое число, если оно целое
                    thickness_int = int(thickness) if float(
                        thickness).is_integer() else thickness

                    # Формируем имя файла с целыми значениями размеров
                    length_int = int(original_length)
                    width_int = int(original_width)

                    if material != 'S':
                        output_file = f"{formatted_id}_{length_int}x{width_int}_{thickness_int}mm_{material}.dxf"
                    else:
                        output_file = f"{formatted_id}_{length_int}x{width_int}_{thickness_int}mm.dxf"

                    logger.info(
                        f"Создается карта раскроя для остатка с ID={remnant_id} → {formatted_id}, файл={output_file}")
                else:
                    # Для целого листа используем счетчик
                    sheet_idx = container_id

                    # Преобразуем thickness в целое число, если оно целое
                    thickness_int = int(thickness) if float(
                        thickness).is_integer() else thickness

                    if material != 'S':
                        output_file = f"sheet_{thickness_int}mm_{material}_{sheet_idx}.dxf"
                    else:
                        output_file = f"sheet_{thickness_int}mm_{sheet_idx}.dxf"
                    logger.info(
                        f"Создается карта раскроя для целого листа: {output_file}")

                # Добавляем заголовок
                add_layout_filename_title(
                    msp, original_length, original_width, output_file)

                # Добавляем список деталей БЕЗ имени файла
                # Не передаем имя файла!
                add_details_list(msp, original_width, details_list)

                # Получаем полный путь с учетом организации по папкам
                organized_file_path = get_organized_file_path(thickness, material, output_file)
                
                # Сохраняем файл в организованную структуру папок
                doc.saveas(organized_file_path)
                logger.info(f"Сохранен файл в организованную структуру: {organized_file_path}")
                layout_count += 1

                # Добавляем контейнер в финальный упаковщик
                final_packer.add_bin(length_with_margin,
                                     width_with_margin, bid=bin_counter)

                # Добавляем все детали в финальный упаковщик
                for rect in packer[0]:
                    final_packer.add_rect(rect.width, rect.height, rect.rid)

                bin_counter += 1

            except Exception as e:
                logger.error(
                    f"Ошибка при создании DXF для контейнера {container_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())

        # Устанавливаем финальный упаковщик для этой комбинации материал/толщина
        packers_by_material[material_key] = final_packer

        # Подсчитываем количество использованных листов
        total_used_sheets += used_full_sheets

        # Удаляем использованные остатки из таблицы материалов
        if used_remnant_ids:
            logger.info(
                f"Удаление {len(used_remnant_ids)} использованных остатков из таблицы")

            # Создаем маску для строк, которые нужно удалить
            before_count = len(current_materials_df)
            delete_mask = (current_materials_df['is_remnant'] == True) & \
                (current_materials_df['remnant_id'].isin(
                    list(used_remnant_ids)))

            # Получаем индексы строк, которые нужно удалить
            delete_indices = current_materials_df[delete_mask].index

            # Удаляем эти строки из таблицы
            current_materials_df = current_materials_df.drop(delete_indices)

            after_count = len(current_materials_df)
            logger.info(
                f"Удалено {before_count - after_count} строк из таблицы материалов")

        # Обновляем таблицу материалов с учетом новых остатков
        std_material_mask = (
            (current_materials_df['thickness_mm'] == thickness) &
            (current_materials_df['material'] == material) &
            (current_materials_df['is_remnant'] == False)
        )

        if std_material_mask.any():
            std_sheet = current_materials_df[std_material_mask].iloc[0]
            sheet_length = std_sheet['sheet_length_mm']
            sheet_width = std_sheet['sheet_width_mm']

            # Обновляем таблицу с передачей размеров листа
            updated_materials = remnants_manager.update_material_table(
                current_materials_df, final_packer, thickness, material,
                used_full_sheets, sheet_length, sheet_width)
            current_materials_df = updated_materials
        else:
            logger.warning(
                f"Не найдены стандартные листы для толщины {thickness} и материала {material}")
            updated_materials = remnants_manager.update_material_table(
                current_materials_df, final_packer, thickness, material, used_full_sheets)
            current_materials_df = updated_materials

    # Перед сохранением таблицы проверяем наличие колонки remnant_id
    if 'remnant_id' not in current_materials_df.columns:
        current_materials_df['remnant_id'] = None
        logger.warning(
            "Перед сохранением добавлена отсутствующая колонка 'remnant_id'")

    # Выводим итоговую статистику
    remnants_count = sum(
        1 for _, row in current_materials_df.iterrows() if row.get('is_remnant', False))
    logger.info(f"Итоговое количество остатков в таблице: {remnants_count}")

    # Сохраняем обновленную таблицу материалов
    remnants_manager.save_material_table(
        current_materials_df, "updated_materials.csv")

    logger.info(
        f"Упаковка завершена. Всего листов: {total_used_sheets}, карт раскроя: {layout_count}")
    logger.info(f"Всего остатков в обновленной таблице: {remnants_count}")

    return packers_by_material, total_used_sheets, layout_count
