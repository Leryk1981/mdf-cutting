import os
from rectpack import newPacker, MaxRectsBlsf, MaxRectsBaf, GuillotineBssfSas, SkylineBl
from .config import logger # Assuming test/config.py exists and is intended
from packer.dxf_writer import ( # Updated import path
    create_new_dxf,
    add_sheet_outline,
    add_detail_to_sheet,
    add_layout_filename_title,
    add_details_list
)
from .constants import (
    DEFAULT_MARGIN,
    DEFAULT_KERF
)


def hybrid_sort_big_first(rectangles):
    """Сортировка деталей для оптимальной упаковки.
    Сначала большие детали, потом средние, потом маленькие."""
    medium, large, small = [], [], []
    for w, h, idx in rectangles:
        if w > 2000:
            large.append((w, h, idx))
        elif w < 800:
            small.append((w, h, idx))
        else:
            medium.append((w, h, idx))
    return (sorted(large, key=lambda x: -x[0]) +
            sorted(medium, key=lambda x: -(x[0] * x[1])) +
            sorted(small, key=lambda x: (-x[0], -x[1])))


def hybrid_sort_medium_first(rectangles):
    """Сортировка деталей для оптимальной упаковки.
    Сначала средние детали, потом большие, потом маленькие (исходный вариант)."""
    medium, large, small = [], [], []
    for w, h, idx in rectangles:
        if w > 2000:
            large.append((w, h, idx))
        elif w < 800:
            small.append((w, h, idx))
        else:
            medium.append((w, h, idx))
    return (sorted(medium, key=lambda x: -(x[0] * x[1])) +
            sorted(large, key=lambda x: -x[0]) +
            sorted(small, key=lambda x: (-x[0], -x[1])))


def prepare_rectangles_for_packing(material_details, kerf, force_rotate_large=True):
    """
    Подготовка прямоугольников для упаковки с опциональным принудительным поворотом больших деталей.

    Args:
        material_details: DataFrame с деталями
        kerf: диаметр фрезы (мм)
        force_rotate_large: принудительно поворачивать большие детали (True/False)

    Returns:
        list: список кортежей (ширина, высота, индекс)
    """
    rects_to_pack = []
    for idx, detail in material_details.iterrows():
        width = detail['length_mm'] + kerf
        height = detail['width_mm'] + kerf

        if width <= 0 or height <= 0:
            print(f"Пропуск {detail['part_id']}: {width}x{height}")
            continue

        quantity = max(1, int(detail.get('quantity', 1)))

        # Если включен принудительный поворот и деталь "длинная"
        if force_rotate_large and width > height * 2:
            # Поворачиваем деталь
            width, height = height, width
            print(f"Поворот детали {detail['part_id']}: {width}x{height}")

        for _ in range(quantity):
            rects_to_pack.append((width, height, idx))

    return rects_to_pack


def test_maxrects_blsf(details_df, materials_df, output_dir=".", pattern_dir="patterns", margin=DEFAULT_MARGIN, kerf=DEFAULT_KERF, sort_mode="big_first", force_rotate_large=True):
    """
    Тестирование упаковки деталей с использованием только алгоритма MaxRectsBlsf.
    Игнорирует остатки и использует только целые листы материала.

    Args:
        details_df: DataFrame с деталями
        materials_df: DataFrame с материалами
        output_dir: директория для сохранения результатов
        pattern_dir: директория с узорами (не используется в тесте)
        margin: отступ от края листа (мм)
        kerf: диаметр фрезы (мм)
        sort_mode: режим сортировки - "big_first" или "medium_first"
        force_rotate_large: если True, большие детали будут принудительно повернуты

    Returns:
        tuple: (словарь упаковщиков, количество использованных листов, количество карт раскроя)
    """
    print(
        f"Запуск тестирования алгоритма MAXRECTS-BLSF (без остатков), режим сортировки: {sort_mode}")
    logger.info(
        f"Запуск тестирования алгоритма MAXRECTS-BLSF (без остатков), режим сортировки: {sort_mode}")

    packers_by_material = {}
    total_used_sheets = 0
    layout_count = 0  # Подсчёт созданных карт раскроя

    # Получаем уникальные комбинации толщины и материала
    unique_combinations = details_df[[
        'thickness_mm', 'material']].drop_duplicates()
    print(f"Найдено {len(unique_combinations)} комбинаций")

    for _, row in unique_combinations.iterrows():
        thickness = row['thickness_mm']
        material = row['material']
        material_key = thickness if material == 'S' else f"{thickness}_{material}"
        print(
            f"\nОбработка: толщина={thickness}, материал={material}, ключ={material_key}")

        # Фильтруем детали для текущей комбинации
        detail_mask = (details_df['thickness_mm'] == thickness) & (
            details_df['material'] == material)
        material_details = details_df[detail_mask].copy()
        if material_details.empty:
            print("Нет деталей для данной комбинации")
            continue

        # Фильтруем материалы для текущей комбинации (только целые листы)
        material_mask = ((materials_df['thickness_mm'] == thickness) &
                         (materials_df['material'] == material) &
                         (materials_df['is_remnant'] == False))
        material_sheets = materials_df[material_mask].copy()
        if material_sheets.empty:
            print("Нет листов для данной комбинации")
            continue

        # Подготовка деталей для упаковки
        material_details = material_details.reset_index(drop=True)
        rects_to_pack = prepare_rectangles_for_packing(
            material_details, kerf, force_rotate_large)

        if not rects_to_pack:
            print("Нет прямоугольников для упаковки")
            continue

        print("Детали для упаковки:")
        for w, h, idx in rects_to_pack:
            print(f" - {material_details.iloc[idx]['part_id']}: {w}x{h}")

        # Получаем размеры целых листов
        full_sheets = [(row['sheet_length_mm'] - 2 * margin, row['sheet_width_mm'] - 2 * margin)
                       for _, row in material_sheets.iterrows()
                       for _ in range(int(row['total_quantity']))]

        print(f"Целые листы: {len(full_sheets)}")
        for w, h in full_sheets:
            print(f" - Лист: {w}x{h}")

        if not full_sheets:
            print("Нет листов для упаковки")
            continue

        # Сортируем детали с использованием выбранного алгоритма сортировки
        if sort_mode == "big_first":
            rects_to_pack = hybrid_sort_big_first(rects_to_pack)
            sort_name = "большие_сначала"
        else:
            rects_to_pack = hybrid_sort_medium_first(rects_to_pack)
            sort_name = "средние_сначала"

        # Создаем упаковщик с алгоритмом MaxRectsBlsf
        packer = newPacker(rotation=True, pack_algo=MaxRectsBlsf)

        # Добавляем целые листы
        for i, (w, h) in enumerate(full_sheets):
            packer.add_bin(w, h, bid=i)

        # Добавляем детали
        for w, h, idx in rects_to_pack:
            packer.add_rect(w, h, idx)

        # Выполняем упаковку
        packer.pack()

        # Подсчитываем использованные листы
        used_sheets = len([bin for bin in packer if bin])
        total_used_sheets += used_sheets
        packers_by_material[material_key] = packer

        print(f"\nРезультаты упаковки для комбинации {material_key}:")
        print(f"Использовано листов: {used_sheets} из {len(full_sheets)}")

        # Генерация DXF файлов
        sheet_idx = 0
        for bin_idx, bin in enumerate(packer):
            if not bin:
                continue

            try:
                # Получаем размеры листа
                sheet_length, sheet_width = full_sheets[bin.bid]
                sheet_length += 2 * margin
                sheet_width += 2 * margin

                # Создаем новый DXF документ
                doc, msp = create_new_dxf()

                # Добавляем контур листа
                add_sheet_outline(msp, sheet_length, sheet_width, margin)

                # Список для информации о деталях
                details_list = []

                # Добавляем детали на лист
                for rect in bin:
                    idx = rect.rid
                    detail = material_details.iloc[idx]
                    orig_width = detail['length_mm']
                    orig_height = detail['width_mm']
                    rect_width = rect.width - kerf
                    rect_height = rect.height - kerf
                    is_rotated = (abs(rect_width - orig_width) >
                                  0.1) or (abs(rect_height - orig_height) > 0.1)
                    detail_rect = {
                        'x': rect.x + margin,
                        'y': rect.y + margin,
                        'width': rect_width,
                        'height': rect_height,
                        'rotated': is_rotated
                    }
                    detail_info = add_detail_to_sheet(
                        msp, detail, detail_rect, kerf)
                    if detail_info:
                        details_list.append(detail_info)

                # Формируем имя файла
                thickness_int = int(thickness) if float(
                    thickness).is_integer() else thickness
                if material != 'S':
                    output_file = f"test_blsf_{thickness_int}mm_{material}_{sort_name}_{sheet_idx}.dxf"
                else:
                    output_file = f"test_blsf_{thickness_int}mm_{sort_name}_{sheet_idx}.dxf"

                # Добавляем заголовок и список деталей
                add_layout_filename_title(
                    msp, sheet_length, sheet_width, output_file)
                add_details_list(msp, sheet_width, details_list)

                # Сохраняем файл
                output_path = os.path.join(output_dir, output_file)
                doc.saveas(output_path)
                print(f"Сохранён файл: {output_path}")
                layout_count += 1
                sheet_idx += 1

            except Exception as e:
                print(f"Ошибка DXF для листа {bin_idx}: {str(e)}")
                logger.error(f"Ошибка DXF для листа {bin_idx}: {str(e)}")

    print(
        f"\nУпаковка завершена. Всего листов: {total_used_sheets}, карт раскроя: {layout_count}")
    logger.info(f"Создано карт раскроя: {layout_count}")

    return packers_by_material, total_used_sheets, layout_count


def test_various_algorithms(details_df, materials_df, output_dir=".", pattern_dir="patterns", margin=DEFAULT_MARGIN, kerf=DEFAULT_KERF, force_rotate_large=True):
    """
    Тестирование разных алгоритмов упаковки из библиотеки rectpack.
    Сравнивает все доступные алгоритмы из библиотеки rectpack:
    - MaxRectsBl (Bottom-Left)
    - MaxRectsBlsf (Bottom-Left Score Fit)
    - MaxRectsBaf (Best Area Fit)
    - GuillotineBssfSas (Best Short Side Fit / Sort Area in Semi-Decreasing)
    - SkylineBl (Bottom-Left)
    - SkylineMwf (Max Width Fit)

    Args:
        details_df: DataFrame с деталями
        materials_df: DataFrame с материалами
        output_dir: директория для сохранения результатов
        pattern_dir: директория с узорами (не используется в тесте)
        margin: отступ от края листа (мм)
        kerf: диаметр фрезы (мм)
        force_rotate_large: если True, большие детали будут принудительно повернуты

    Returns:
        dict: словарь с результатами для каждого алгоритма
    """
    print("Запуск сравнительного тестирования различных алгоритмов упаковки")
    logger.info(
        "Запуск сравнительного тестирования различных алгоритмов упаковки")
    if force_rotate_large:
        print("Включен режим принудительного поворота больших деталей (длина > 2000 мм)")
        logger.info(
            "Включен режим принудительного поворота больших деталей (длина > 2000 мм)")

    # Импортируем все доступные алгоритмы из rectpack
    from rectpack import (
        MaxRectsBl, MaxRectsBlsf, MaxRectsBaf,
        GuillotineBssfSas,
        SkylineBl, SkylineMwf
    )

    algorithms = {
        "MaxRectsBl": MaxRectsBl,        # Bottom-Left
        "MaxRectsBlsf": MaxRectsBlsf,    # Bottom-Left Score Fit
        "MaxRectsBaf": MaxRectsBaf,      # Best Area Fit
        # Best Short Side Fit / Sort Area in Semi-Decreasing
        "GuillotineBssfSas": GuillotineBssfSas,
        "SkylineBl": SkylineBl,          # Bottom-Left
        "SkylineMwf": SkylineMwf         # Max Width Fit
    }

    results = {}

    # Проходим по всем доступным алгоритмам
    for algo_name, algo_class in algorithms.items():
        print(f"\n\n=== Тестирование алгоритма {algo_name} ===\n")
        logger.info(f"=== Тестирование алгоритма {algo_name} ===")

        results[algo_name] = {}
        total_used_sheets = 0
        layout_count = 0

        # Получаем уникальные комбинации толщины и материала
        unique_combinations = details_df[[
            'thickness_mm', 'material']].drop_duplicates()

        for _, row in unique_combinations.iterrows():
            thickness = row['thickness_mm']
            material = row['material']
            material_key = thickness if material == 'S' else f"{thickness}_{material}"
            print(
                f"\nОбработка: толщина={thickness}, материал={material}, ключ={material_key}")

            # Фильтруем детали для текущей комбинации
            detail_mask = (details_df['thickness_mm'] == thickness) & (
                details_df['material'] == material)
            material_details = details_df[detail_mask].copy()
            if material_details.empty:
                continue

            # Фильтруем материалы для текущей комбинации (только целые листы)
            material_mask = ((materials_df['thickness_mm'] == thickness) &
                             (materials_df['material'] == material) &
                             (materials_df['is_remnant'] == False))
            material_sheets = materials_df[material_mask].copy()
            if material_sheets.empty:
                continue

            # Подготовка деталей для упаковки с принудительным поворотом больших деталей
            material_details = material_details.reset_index(drop=True)
            rects_to_pack = prepare_rectangles_for_packing(
                material_details, kerf, force_rotate_large)

            if not rects_to_pack:
                continue

            # Получаем размеры целых листов
            full_sheets = [(row['sheet_length_mm'] - 2 * margin, row['sheet_width_mm'] - 2 * margin)
                           for _, row in material_sheets.iterrows()
                           for _ in range(int(row['total_quantity']))]

            if not full_sheets:
                continue

            # Сортируем детали с использованием гибридного алгоритма сортировки
            rects_to_pack = hybrid_sort_medium_first(rects_to_pack)

            # Создаем упаковщик с текущим алгоритмом
            packer = newPacker(rotation=True, pack_algo=algo_class)

            # Добавляем целые листы
            for i, (w, h) in enumerate(full_sheets):
                packer.add_bin(w, h, bid=i)

            # Добавляем детали
            for w, h, idx in rects_to_pack:
                packer.add_rect(w, h, idx)

            # Выполняем упаковку
            packer.pack()

            # Подсчитываем использованные листы
            used_sheets = len([bin for bin in packer if bin])
            total_used_sheets += used_sheets
            results[algo_name][material_key] = used_sheets

            print(
                f"Результаты для {material_key}: использовано листов {used_sheets} из {len(full_sheets)}")

            # Генерация DXF файлов
            sheet_idx = 0
            for bin_idx, bin in enumerate(packer):
                if not bin:
                    continue

                try:
                    # Получаем размеры листа
                    sheet_length, sheet_width = full_sheets[bin.bid]
                    sheet_length += 2 * margin
                    sheet_width += 2 * margin

                    # Создаем новый DXF документ
                    doc, msp = create_new_dxf()

                    # Добавляем контур листа
                    add_sheet_outline(msp, sheet_length, sheet_width, margin)

                    # Список для информации о деталях
                    details_list = []

                    # Добавляем детали на лист
                    for rect in bin:
                        idx = rect.rid
                        detail = material_details.iloc[idx]
                        orig_width = detail['length_mm']
                        orig_height = detail['width_mm']
                        rect_width = rect.width - kerf
                        rect_height = rect.height - kerf
                        is_rotated = (abs(rect_width - orig_width) >
                                      0.1) or (abs(rect_height - orig_height) > 0.1)
                        detail_rect = {
                            'x': rect.x + margin,
                            'y': rect.y + margin,
                            'width': rect_width,
                            'height': rect_height,
                            'rotated': is_rotated
                        }
                        detail_info = add_detail_to_sheet(
                            msp, detail, detail_rect, kerf)
                        if detail_info:
                            details_list.append(detail_info)

                    # Формируем имя файла
                    thickness_int = int(thickness) if float(
                        thickness).is_integer() else thickness
                    rotate_suffix = "_rotated" if force_rotate_large else ""
                    if material != 'S':
                        output_file = f"test_{algo_name}_{thickness_int}mm_{material}{rotate_suffix}_{sheet_idx}.dxf"
                    else:
                        output_file = f"test_{algo_name}_{thickness_int}mm{rotate_suffix}_{sheet_idx}.dxf"

                    # Добавляем заголовок и список деталей
                    add_layout_filename_title(
                        msp, sheet_length, sheet_width, output_file)
                    add_details_list(msp, sheet_width, details_list)

                    # Сохраняем файл
                    output_path = os.path.join(output_dir, output_file)
                    doc.saveas(output_path)
                    print(f"Сохранён файл: {output_path}")
                    layout_count += 1
                    sheet_idx += 1

                except Exception as e:
                    print(f"Ошибка DXF для листа {bin_idx}: {str(e)}")
                    logger.error(f"Ошибка DXF для листа {bin_idx}: {str(e)}")

        results[algo_name]['total_sheets'] = total_used_sheets
        results[algo_name]['layout_count'] = layout_count
        print(f"\n=== Результаты для алгоритма {algo_name} ===")
        print(f"Всего использовано листов: {total_used_sheets}")
        print(f"Создано карт раскроя: {layout_count}")
        logger.info(
            f"Алгоритм {algo_name}: листов {total_used_sheets}, карт {layout_count}")

    # Сравнительная таблица результатов
    print("\n=== Сравнение алгоритмов ===")
    print("| Алгоритм | Листов | Карт раскроя |")
    print("|----------|--------|-------------|")
    for algo_name, result in results.items():
        print(
            f"| {algo_name} | {result['total_sheets']} | {result['layout_count']} |")

    return results
