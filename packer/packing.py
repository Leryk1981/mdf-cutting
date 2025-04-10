import os
from rectpack import newPacker, MaxRectsBlsf
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
from .constants import (
    STANDARD_SHEET_LENGTH,
    STANDARD_SHEET_WIDTH,
    DEFAULT_MARGIN,
    DEFAULT_KERF,
    MATERIALS_REQUIRED_COLUMNS,
    DETAILS_REQUIRED_COLUMNS
)


def hybrid_sort(rectangles):
    """Сортировка деталей для HybridMaxRects."""
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


def pack_and_generate_dxf(details_df, materials_df, pattern_dir="patterns", margin=DEFAULT_MARGIN, kerf=DEFAULT_KERF):
    """
    Упаковывает детали и генерирует DXF файлы с приоритетом остатков.

    Args:
        details_df: DataFrame с деталями
        materials_df: DataFrame с материалами
        pattern_dir: директория с узорами
        margin: отступ от края листа (мм)
        kerf: диаметр фрезы (мм)

    Returns:
        tuple: (словарь упаковщиков, количество использованных листов)
    """
    print("Запуск упаковки с полным приоритетом остатков")
    logger.info("Запуск упаковки с полным приоритетом остатков")

    packers_by_material = {}
    total_used_sheets = 0
    remnants_manager = RemnantsManager(margin=margin, kerf=kerf)
    current_materials_df = materials_df.copy()
    layout_count = 0  # Подсчёт созданных карт раскроя

    for col in MATERIALS_REQUIRED_COLUMNS:
        if col not in current_materials_df.columns:
            logger.error(f"Отсутствует колонка '{col}' в materials_df")
            raise ValueError(f"Missing column '{col}' in materials_df")
    for col in DETAILS_REQUIRED_COLUMNS:
        if col not in details_df.columns:
            logger.error(f"Отсутствует колонка '{col}' в details_df")
            raise ValueError(f"Missing column '{col}' in details_df")

    unique_combinations = details_df[[
        'thickness_mm', 'material']].drop_duplicates()
    print(f"Найдено {len(unique_combinations)} комбинаций")

    for _, row in unique_combinations.iterrows():
        thickness = row['thickness_mm']
        material = row['material']
        material_key = thickness if material == 'S' else f"{thickness}_{material}"
        print(
            f"\nОбработка: толщина={thickness}, материал={material}, ключ={material_key}")

        detail_mask = (details_df['thickness_mm'] == thickness) & (
            details_df['material'] == material)
        material_details = details_df[detail_mask].copy()
        if material_details.empty:
            print("Нет деталей")
            continue

        material_mask = (current_materials_df['thickness_mm'] == thickness) & (
            current_materials_df['material'] == material)
        material_sheets = current_materials_df[material_mask].copy()
        if material_sheets.empty:
            print("Нет листов")
            continue

        rects_to_pack = []
        material_details = material_details.reset_index(drop=True)
        for idx, detail in material_details.iterrows():
            packing_width = detail['length_mm'] + kerf
            packing_height = detail['width_mm'] + kerf
            if packing_width <= 0 or packing_height <= 0:
                print(
                    f"Пропуск {detail['part_id']}: {packing_width}x{packing_height}")
                continue
            quantity = max(1, int(detail.get('quantity', 1)))
            for _ in range(quantity):
                rects_to_pack.append((packing_width, packing_height, idx))

        if not rects_to_pack:
            print("Нет прямоугольников")
            continue

        print("Детали для упаковки:")
        for w, h, idx in rects_to_pack:
            print(f" - {material_details.iloc[idx]['part_id']}: {w}x{h}")

        # Получаем остатки и целые листы
        remnants = [(row['sheet_length_mm'] - 2 * margin, row['sheet_width_mm'] - 2 * margin)
                    for _, row in material_sheets[material_sheets['is_remnant'] == True].iterrows()
                    for _ in range(int(row['total_quantity']))]
        full_sheets = [(row['sheet_length_mm'] - 2 * margin, row['sheet_width_mm'] - 2 * margin)
                       for _, row in material_sheets[material_sheets['is_remnant'] == False].iterrows()
                       for _ in range(int(row['total_quantity']))]

        print(f"Остатки: {len(remnants)}")
        for w, h in remnants:
            print(f" - Остаток: {w}x{h}")
        print(f"Целые листы: {len(full_sheets)}")
        for w, h in full_sheets:
            print(f" - Лист: {w}x{h}")

        if not remnants and not full_sheets:
            print("Нет контейнеров")
            continue

        # Сортируем детали
        rects_to_pack = hybrid_sort(rects_to_pack)
        final_packer = newPacker(rotation=True, pack_algo=MaxRectsBlsf)
        bin_info = []
        packed_rects = set()
        bid = 0

        # Фаза 1: Упаковка только остатков
        if remnants:
            remnant_packer = newPacker(rotation=True, pack_algo=MaxRectsBlsf)
            for w, h in remnants:
                remnant_packer.add_bin(w, h)
            for w, h, idx in rects_to_pack:
                remnant_packer.add_rect(w, h, idx)

            remnant_packer.pack()
            print("\nФаза 1: Упаковка остатков")
            for bin in remnant_packer:
                if bin.rect_list():
                    fill_percent = (
                        sum(rect.width * rect.height for rect in bin) / (bin.width * bin.height)) * 100
                    print(
                        f"Остаток {bid} ({bin.width}x{bin.height}): заполнение {fill_percent:.2f}%")
                    final_packer.add_bin(bin.width, bin.height, bid=bid)
                    bin_info.append((bid, bin.width, bin.height))
                    for rect in bin:
                        final_packer.add_rect(
                            rect.width, rect.height, rect.rid)
                        packed_rects.add(rect.rid)
                        print(
                            f" - Упакована деталь {material_details.iloc[rect.rid]['part_id']}: {rect.width}x{rect.height}")
                    bid += 1

        # Фаза 2: Упаковка оставшихся деталей в целые листы
        remaining_rects = [(w, h, idx)
                           for w, h, idx in rects_to_pack if idx not in packed_rects]
        if remaining_rects and full_sheets:
            full_sheet_packer = newPacker(
                rotation=True, pack_algo=MaxRectsBlsf)
            for w, h in full_sheets:
                full_sheet_packer.add_bin(w, h)
            for w, h, idx in remaining_rects:
                full_sheet_packer.add_rect(w, h, idx)

            full_sheet_packer.pack()
            print("\nФаза 2: Упаковка целых листов")
            for bin in full_sheet_packer:
                if bin.rect_list():
                    fill_percent = (
                        sum(rect.width * rect.height for rect in bin) / (bin.width * bin.height)) * 100
                    print(
                        f"Лист {bid} ({bin.width}x{bin.height}): заполнение {fill_percent:.2f}%")
                    final_packer.add_bin(bin.width, bin.height, bid=bid)
                    bin_info.append((bid, bin.width, bin.height))
                    for rect in bin:
                        final_packer.add_rect(
                            rect.width, rect.height, rect.rid)
                        packed_rects.add(rect.rid)
                        print(
                            f" - Упакована деталь {material_details.iloc[rect.rid]['part_id']}: {rect.width}x{rect.height}")
                    bid += 1

        final_packer.pack()
        used_sheets = len([bin for bin in final_packer if bin])
        total_used_sheets += used_sheets
        packers_by_material[material_key] = final_packer

        # Обновляем таблицу материалов
        updated_materials = remnants_manager.update_material_table(
            current_materials_df, final_packer, thickness, material, used_sheets,
            STANDARD_SHEET_LENGTH, STANDARD_SHEET_WIDTH)
        current_materials_df = updated_materials  # Обновляем текущую таблицу

        # Генерация DXF
        bin_idx = 0
        bin_map = {bid: (w + 2 * margin, h + 2 * margin)
                   for bid, w, h in bin_info}
        for bin in final_packer:
            if not bin:
                continue
            try:
                doc, msp = create_new_dxf()
                sheet_length, sheet_width = bin_map[bin.bid]
                add_sheet_outline(msp, sheet_length, sheet_width, margin)
                details_list = []

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

                output_file = (f"final_layout_{thickness}mm_{material}_{bin_idx}_HybridMaxRectsRemnants.dxf"
                               if material != 'S'
                               else f"final_layout_{thickness}mm_{bin_idx}_HybridMaxRectsRemnants.dxf")
                add_layout_filename_title(
                    msp, sheet_length, sheet_width, output_file)
                add_details_list(msp, sheet_width, details_list)
                doc.saveas(output_file)
                print(f"Сохранён файл: {output_file}")
                layout_count += 1
                bin_idx += 1
            except Exception as e:
                print(f"Ошибка DXF для листа {bin_idx}: {str(e)}")
                logger.error(f"Ошибка DXF для листа {bin_idx}: {str(e)}")

    remnants_manager.save_material_table(
        current_materials_df, "updated_materials.csv")
    print(
        f"Упаковка завершена. Всего листов: {total_used_sheets}, карт раскроя: {layout_count}")
    logger.info(f"Создано карт раскроя: {layout_count}")
    return packers_by_material, total_used_sheets
