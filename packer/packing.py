import os
from rectpack import newPacker, MaxRectsBssf
from .config import logger
from .patterns import load_patterns
from .dxf_writer import (
    create_new_dxf,
    add_sheet_outline,
    add_detail_to_sheet,
    add_layout_filename_title,
    add_details_list
)
from .remnants import RemnantsManager
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


def _prepare_details_for_packing(details_df_for_material, kerf):
    """
    Prepares a list of rectangles (details) with unique IDs for packing.
    Each rectangle's dimensions are increased by the kerf value.

    Args:
        details_df_for_material (pd.DataFrame): DataFrame containing details for a specific material/thickness.
                                                Requires columns: 'part_id', 'length_mm', 'width_mm', 'quantity'.
        kerf (float): Kerf value (cutter diameter) to be added to detail dimensions.

    Returns:
        list[tuple[float, float, tuple[int, int]]]:
            A list of tuples, where each tuple represents a detail instance:
            (packing_width, packing_height, unique_detail_id).
            'packing_width' is detail_length + kerf.
            'packing_height' is detail_width + kerf.
            'unique_detail_id' is a tuple (original_detail_index, copy_counter).
            Returns an empty list if no valid details are found.
    """
    rects_to_pack = []
    unique_id_counter = 0 # Counter to make each detail copy unique
    details_df_for_material = details_df_for_material.reset_index(drop=True)

    for idx, detail in details_df_for_material.iterrows():
        detail_length = detail['length_mm']
        detail_width = detail['width_mm']
        part_id = detail['part_id']

        packing_width = detail_length + kerf
        packing_height = detail_width + kerf

        if packing_width <= 0 or packing_height <= 0:
            logger.warning(
                f"Skipping detail {part_id} due to invalid packing dimensions: {packing_width}x{packing_height}"
            )
            continue

        quantity = max(1, int(detail.get('quantity', 1)))
        logger.info(f"Processing detail ID={part_id}, " +
                    f"original size={detail_length}x{detail_width}, quantity={quantity}")

        for _ in range(quantity): # Use _ if q is not used
            unique_detail_id = (idx, unique_id_counter)
            unique_id_counter += 1
            rects_to_pack.append(
                (packing_width, packing_height, unique_detail_id))
            # Reduced verbosity for logging each copy, can be re-enabled if needed for deep debugging
            # logger.info(f"Added copy {q+1}/{quantity} of detail {part_id} " +
            #             f"with unique ID={unique_detail_id}")

    if not rects_to_pack:
        logger.info("No details to pack for the current material configuration.")
    else:
        logger.info(f"Prepared {len(rects_to_pack)} detail instances for packing.")
    return rects_to_pack


def _prepare_materials(sheets_df_for_material, margin):
    """
    Prepares lists of remnant and full sheet dictionaries from the material sheets DataFrame.
    Each dictionary includes original dimensions and dimensions with margin for packing.

    Args:
        sheets_df_for_material (pd.DataFrame): DataFrame containing sheet/remnant data for a specific material/thickness.
                                               Requires columns: 'is_remnant', 'remnant_id',
                                               'sheet_length_mm', 'sheet_width_mm', 'total_quantity'.
        margin (float): Margin to be subtracted from sheet/remnant dimensions for packing area.

    Returns:
        tuple[list[dict], dict, list[dict]]:
            - list[dict]: `remnants_list` - A list of dictionaries, each representing a remnant instance.
                          Each dict contains: 'width', 'length', 'remnant_id', 'width_with_margin', 'length_with_margin'.
            - dict: `remnant_lookup` - A dictionary mapping remnant_id to its properties (first encountered if IDs are not unique).
            - list[dict]: `full_sheets_list` - A list of dictionaries, each representing a full sheet instance.
                          Each dict contains: 'width', 'length', 'width_with_margin', 'length_with_margin'.
    """
    remnants_list = []
    remnant_lookup = {} # For quick lookup of remnant properties by ID

    # Process remnants
    remnant_rows = sheets_df_for_material[sheets_df_for_material['is_remnant'] == True].copy()
    logger.info(f"Found {len(remnant_rows)} types of remnants for this material.")

    for _, remnant_row in remnant_rows.iterrows():
        remnant_id = remnant_row.get('remnant_id', None)
        if remnant_id is None:
            logger.warning(f"Skipping a remnant entry due to missing remnant_id: {remnant_row}")
            continue

        length = float(remnant_row['sheet_length_mm'])
        width = float(remnant_row['sheet_width_mm'])

        if length <= 0 or width <= 0:
            logger.warning(
                f"Skipping remnant with ID={remnant_id} due to invalid dimensions: {length}x{width}"
            )
            continue

        # Each remnant type can have multiple instances (total_quantity)
        for _ in range(int(remnant_row['total_quantity'])):
            remnant_properties = {
                'width': width,
                'length': length,
                'remnant_id': remnant_id,
                'width_with_margin': remnant_width - 2 * margin,
                'length_with_margin': remnant_length - 2 * margin
            }
            remnants_list.append(remnant_properties)
            if remnant_id not in remnant_lookup: # Store properties for the first encountered instance of this ID
                remnant_lookup[remnant_id] = remnant_properties
            # logger.info(f"Added remnant instance with ID={remnant_id}, dimensions={length}x{width}") # Can be verbose

    logger.info(f"Prepared {len(remnants_list)} total remnant instances.")
    if remnants_list:
        remnants_list.sort(key=lambda r: r['width'] * r['length'], reverse=True)
        logger.info("Remnants sorted by area in descending order.")

    # Process full sheets
    full_sheets_list = []
    full_sheet_rows = sheets_df_for_material[sheets_df_for_material['is_remnant'] == False]
    logger.info(f"Found {len(full_sheet_rows)} types of full sheets for this material.")

    for _, sheet_row in full_sheet_rows.iterrows():
        length = float(sheet_row['sheet_length_mm'])
        width = float(sheet_row['sheet_width_mm'])

        if length <= 0 or width <= 0:
            logger.warning(
                f"Skipping a full sheet entry due to invalid dimensions: {length}x{width}"
            )
            continue

        # Each sheet type can have multiple instances
        for _ in range(int(sheet_row['total_quantity'])):
            full_sheets_list.append({
                'width': width,
                'length': length,
                'width_with_margin': sheet_width - 2 * margin,
                'length_with_margin': sheet_length - 2 * margin
            })
            # logger.info(f"Added full sheet instance, dimensions={length}x{width}") # Can be verbose

    logger.info(f"Prepared {len(full_sheets_list)} total full sheet instances.")
    return remnants_list, remnant_lookup, full_sheets_list


def _pack_into_remnants(material_remnants, rects_to_pack, margin):
    """
    Packs details into available remnant sheets using MaxRectsBaf algorithm.
    Attempts to fill remnants one by one.

    Args:
        material_remnants (list[dict]): List of remnant dictionaries (properties).
        rects_to_pack (list[tuple]): List of tuples (width, height, id) for all details of the current material.
        margin (float): Margin used for packing (already accounted for in remnant dimensions).

    Returns:
        tuple[list[tuple[str, any, object]], set[any]]:
            - `packed_remnant_layouts`: List of tuples ("remnant", remnant_id, packer_instance) for successfully used remnants.
            - `used_remnant_ids`: Set of remnant_ids that were used and had details packed into them.
    """
    from rectpack import MaxRectsBaf

    packed_remnant_layouts = []
    used_remnant_ids = set()
    # Tracks detail IDs that have been successfully packed into *any* remnant in this phase
    detail_ids_packed_in_remnants_phase = set()

    logger.info("\nPhase 1: Packing into Remnants")

    for remnant_props in material_remnants:
        remnant_id = remnant_props['remnant_id']
        logger.info(f"Attempting to pack into remnant ID={remnant_id}")

        packer = newPacker(rotation=True, pack_algo=MaxRectsBaf)
        packer.add_bin(remnant_props['length_with_margin'], remnant_props['width_with_margin'])

        # Filter details: only try to pack those not already packed in a *previous* remnant (in this phase)
        rects_for_this_remnant = []
        for w, h, unique_detail_id in rects_to_pack:
            if unique_detail_id not in detail_ids_packed_in_remnants_phase:
                 rects_for_this_remnant.append((w, h, unique_detail_id))

        if not rects_for_this_remnant:
            logger.info(f"No remaining details to pack for remnant ID={remnant_id}.")
            continue # All details for this material were packed in previous remnants

        for w, h, detail_id_tuple in rects_for_this_remnant:
            packer.add_rect(w, h, detail_id_tuple)

        packer.pack()

        # Check if this specific remnant packer actually packed any items
        if len(packer) > 0 and packer[0] and len(packer[0]) > 0:
            logger.info(f"Successfully packed {len(packer[0])} details into remnant ID={remnant_id}.")
            packed_remnant_layouts.append(("remnant", remnant_id, packer))
            used_remnant_ids.add(remnant_id)
            # Add the newly packed detail IDs to the set for this phase
            for rect in packer[0]:
                detail_ids_packed_in_remnants_phase.add(rect.rid)
        else:
            logger.info(f"Remnant ID={remnant_id} was not used or could not pack any details.")

    logger.info(f"Finished packing into remnants. Used {len(used_remnant_ids)} remnants.")
    return packed_remnant_layouts, used_remnant_ids


def _get_remaining_rects(all_rects, packed_detail_ids_set):
    """
    Filters a list of rectangles to exclude those whose IDs are in the provided set.

    Args:
        all_rects (list[tuple[float, float, tuple[int, int]]]): The initial list of rectangles.
        packed_detail_ids_set (set[tuple[int, int]]): A set of unique_detail_ids that have already been packed.

    Returns:
        list[tuple[float, float, tuple[int, int]]]: A new list containing only the rectangles not yet packed.
    """
    return [rect for rect in all_rects if rect[2] not in packed_detail_ids_set]


def _pack_into_full_sheets(material_full_sheets, all_rects_for_material, detail_ids_packed_in_remnants, margin):
    """
    Packs remaining details into available full sheets using MaxRectsBssf algorithm.

    Args:
        material_full_sheets (list[dict]): List of full sheet dictionaries (properties).
        all_rects_for_material (list[tuple]): Original list of all (width, height, id) tuples for details of the current material.
        detail_ids_packed_in_remnants (set[tuple[int,int]]): Set of unique_detail_ids of details already packed (e.g., in remnants).
        margin (float): Margin for packing (already accounted for in sheet dimensions).

    Returns:
        tuple[list[tuple[str, int, object]], int]:
            - `packed_sheet_layouts`: List of tuples ("sheet", sheet_index, packer_instance) for successfully used sheets.
            - `used_full_sheets_count`: Number of full sheets used in this phase.
    """
    from rectpack import MaxRectsBssf

    packed_sheet_layouts = []
    used_full_sheets_count = 0

    # Determine details that still need packing after remnant phase
    rects_to_pack_in_sheets = _get_remaining_rects(all_rects_for_material, detail_ids_packed_in_remnants)

    logger.info("\nPhase 2: Packing into Full Sheets")
    logger.info(f"Attempting to pack {len(rects_to_pack_in_sheets)} details into full sheets.")

    if rects_to_pack_in_sheets and material_full_sheets:
        # Tracks detail IDs packed within this full sheet packing phase (across multiple sheets)
        detail_ids_packed_in_sheets_phase = set()

        for sheet_idx, sheet_props in enumerate(material_full_sheets):
            # Details that are not in remnants AND not in *previous sheets of this phase*
            current_rects_for_this_sheet = _get_remaining_rects(rects_to_pack_in_sheets, detail_ids_packed_in_sheets_phase)

            if not current_rects_for_this_sheet:
                logger.info("All remaining details have been packed into previous sheets. Stopping full sheet packing.")
                break # No more details left to pack into any subsequent sheet

            packer = newPacker(rotation=True, pack_algo=MaxRectsBssf)
            packer.add_bin(sheet_props['length_with_margin'], sheet_props['width_with_margin'])

            for w, h, detail_id_tuple in current_rects_for_this_sheet:
                packer.add_rect(w, h, detail_id_tuple)

            packer.pack()

            if len(packer) > 0 and packer[0] and len(packer[0]) > 0:
                packed_sheet_layouts.append(("sheet", sheet_idx, packer))
                used_full_sheets_count += 1

                newly_packed_ids_this_sheet = set()
                for rect in packer[0]:
                    newly_packed_ids_this_sheet.add(rect.rid)

                detail_ids_packed_in_sheets_phase.update(newly_packed_ids_this_sheet)
                logger.info(
                    f"Sheet {sheet_idx}: packed {len(newly_packed_ids_this_sheet)} details. "
                    f"Total details packed in sheets so far: {len(detail_ids_packed_in_sheets_phase)}."
                )
            else:
                 logger.info(f"Sheet {sheet_idx} was not used or could not pack any remaining details.")

    logger.info(f"Finished packing into full sheets. Used {used_full_sheets_count} full sheets.")
    return packed_sheet_layouts, used_full_sheets_count


def _generate_dxf_files_for_layouts(
    layouts_for_material, details_for_current_material,
    material_full_sheets_props, material_remnants_lookup,
    thickness, material, margin, kerf, total_layout_count_so_far):
    """
    Generates DXF files for each layout (packed sheet or remnant).
    Also aggregates all packed items into a final packer for the material.

    Args:
        layouts_for_material (list[tuple[str, any, object]]):
            List of tuples (container_type, container_id, packer_instance).
            container_type is "remnant" or "sheet".
            container_id is remnant_id or sheet_index.
        details_for_current_material (pd.DataFrame): DataFrame of details for the current material.
        material_full_sheets_props (list[dict]): List of properties for full sheets (for original dimension lookup).
        material_remnants_lookup (dict): Dict mapping remnant_id to remnant properties.
        thickness (float | str): Thickness of the material.
        material (str): Name/code of the material.
        margin (float): Margin value used in packing.
        kerf (float): Kerf value used for details.
        total_layout_count_so_far (int): Current total count of generated DXF layouts across all materials.

    Returns:
        tuple[object, int]:
            - `final_packer_for_material`: A single `Packer` instance containing all packed items from all layouts for this material.
            - `updated_total_layout_count`: Incremented total layout count.
    """
    logger.info("\nPhase 3: Generating DXF Files and Finalizing Material Packer")
    final_packer_for_material = newPacker(rotation=True, pack_algo=MaxRectsBssf)

    # Use a unique bin ID for each layout added to the final_packer_for_material
    # This ensures that items from different physical sheets/remnants are in different bins in the final packer.
    final_packer_bin_id_counter = 0
    layouts_generated_this_material = 0

    for container_type, container_id, packer in layouts_for_material:
        # Ensure the packer for this layout actually contains packed items
        if not (len(packer) > 0 and packer[0] and len(packer[0]) > 0):
            logger.info(f"Skipping empty packer for {container_type} ID {container_id} during DXF generation.")
            continue

        is_remnant_layout = (container_type == "remnant")
        original_sheet_width, original_sheet_length = 0, 0

        if is_remnant_layout:
            remnant_props = material_remnants_lookup.get(container_id)
            if not remnant_props:
                logger.error(f"Could not find properties for remnant ID={container_id} for DXF generation. Skipping.")
                continue
            original_sheet_width = remnant_props['width']
            original_sheet_length = remnant_props['length']
        else: # sheet layout
            sheet_idx = container_id
            if sheet_idx >= len(material_full_sheets_props):
                logger.error(f"Sheet index {sheet_idx} is out of bounds for DXF generation. Skipping.")
                continue
            sheet_props = material_full_sheets_props[sheet_idx]
            original_sheet_width = sheet_props['width']
            original_sheet_length = sheet_props['length']

        try:
            doc, msp = create_new_dxf()
            add_sheet_outline(msp, original_sheet_length, original_sheet_width, margin)
            dxf_detail_items_list = [] # For the list of parts in the DXF file text

            for rect in packer[0]: # Iterate over packed rectangles in this layout
                # rect.rid is the unique_detail_id (original_detail_index, copy_counter)
                original_detail_index = rect.rid[0]
                detail_data = details_for_current_material.iloc[original_detail_index]

                # Actual dimensions of the part (after subtracting kerf from packing dimensions)
                part_actual_length = rect.width - kerf
                part_actual_width = rect.height - kerf

                # Determine if the part was rotated by comparing packed dimensions with original dimensions
                # (accounting for kerf)
                is_rotated = (abs(part_actual_length - detail_data['length_mm']) > 0.1) or \
                               (abs(part_actual_width - detail_data['width_mm']) > 0.1)

                # Information for add_detail_to_sheet function
                dxf_rect_details = {
                    'x': rect.x + margin,
                    'y': rect.y + margin,
                    'width': rect.width, # Pass packing width (part_actual_length + kerf)
                    'height': rect.height, # Pass packing height (part_actual_width + kerf)
                    'rotated': is_rotated
                }
                # Add detail to DXF and get its info for the list
                dxf_detail_list_item = add_detail_to_sheet(msp, detail_data, dxf_rect_details, kerf)
                if dxf_detail_list_item:
                    dxf_detail_items_list.append(dxf_detail_list_item)

                # logger.info(f"Added detail {detail_data['part_id']} (copy ID: {rect.rid[1]}) " +
                #             f"to DXF for {container_type} {container_id}") # Can be verbose

            # Format filename
            thickness_str = str(int(thickness)) if float(thickness).is_integer() else str(thickness)
            length_str = str(int(original_sheet_length))
            width_str = str(int(original_sheet_width))

            if is_remnant_layout:
                formatted_remnant_id = format_remnant_id(container_id)
                output_file = f"{formatted_remnant_id}_{length_str}x{width_str}_{thickness_str}mm"
                if material != 'S': # Assuming 'S' is a standard material not needing name in file
                    output_file += f"_{material}"
                output_file += ".dxf"
                logger.info(f"Generating DXF for remnant ID={container_id} (formatted as {formatted_remnant_id}), file: {output_file}")
            else: # sheet layout
                output_file = f"sheet_{thickness_str}mm"
                if material != 'S':
                    output_file += f"_{material}"
                output_file += f"_{container_id}.dxf" # container_id is sheet_idx here
                logger.info(f"Generating DXF for full sheet index {container_id}, file: {output_file}")

            add_layout_filename_title(msp, original_sheet_length, original_sheet_width, output_file)
            add_details_list(msp, original_sheet_width, dxf_detail_items_list) # Use original_sheet_width for positioning
            doc.saveas(output_file)
            logger.info(f"Saved DXF file: {output_file}")
            layouts_generated_this_material += 1

            # Add this layout's packed items to the final_packer_for_material
            # The bin dimensions for final_packer should be the same as the ones used for packing this layout
            # (i.e., dimensions with margin)
            layout_bin_width = packer.bin_width(0)
            layout_bin_height = packer.bin_height(0)

            final_packer_for_material.add_bin(layout_bin_width, layout_bin_height, bid=final_packer_bin_id_counter)
            for rect in packer[0]: # rect dimensions already include kerf
                final_packer_for_material.add_rect(rect.width, rect.height, rect.rid, bid=final_packer_bin_id_counter)
            final_packer_bin_id_counter += 1

        except Exception as e:
            logger.error(f"Error generating DXF for {container_type} ID {container_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    updated_total_layout_count = total_layout_count_so_far + layouts_generated_this_material
    logger.info(f"Generated {layouts_generated_this_material} DXF files for material {material}_{thickness}.")
    return final_packer_for_material, updated_total_layout_count


def pack_and_generate_dxf(details_df, materials_df, pattern_dir="patterns", margin=DEFAULT_MARGIN, kerf=DEFAULT_KERF):
    """
    Main function to pack details onto material sheets (prioritizing remnants) and generate DXF layout files.

    Args:
        details_df (pd.DataFrame): DataFrame with details to be packed.
                                   Required columns: 'thickness_mm', 'material', 'part_id', 'length_mm', 'width_mm', 'quantity'.
        materials_df (pd.DataFrame): DataFrame with available materials (sheets and remnants).
                                     Required columns: 'thickness_mm', 'material', 'is_remnant', 'remnant_id',
                                     'sheet_length_mm', 'sheet_width_mm', 'total_quantity'.
        pattern_dir (str, optional): Directory for patterns (currently unused in this scope). Defaults to "patterns".
        margin (float, optional): Default margin for sheet packing. Defaults to DEFAULT_MARGIN.
        kerf (float, optional): Default kerf (cutter diameter). Defaults to DEFAULT_KERF.

    Returns:
        tuple[dict, int, int]:
            - `packers_by_material` (dict): Dictionary mapping material_key to the final `Packer` object for that material.
            - `total_used_sheets_overall` (int): Total number of full sheets used across all materials.
            - `total_layout_count` (int): Total number of DXF layout files generated.
    """
    # Note: rectpack.MaxRectsBaf and rectpack.MaxRectsBssf are imported within helper functions where needed.

    logger.info("Starting packing process with remnant priority.")

    packers_by_material = {}
    total_used_sheets_overall = 0
    remnants_manager = RemnantsManager(margin=margin, kerf=kerf) # Used for updating material table with new remnants
    current_materials_df = materials_df.copy() # Make a copy to modify during processing
    total_layout_count = 0

    # --- Initial Data Validation ---
    for col in MATERIALS_REQUIRED_COLUMNS:
        if col not in current_materials_df.columns:
            logger.error(f"Missing required column '{col}' in materials_df.")
            raise ValueError(f"Missing column '{col}' in materials_df")
    for col in DETAILS_REQUIRED_COLUMNS:
        if col not in details_df.columns:
            logger.error(f"Missing required column '{col}' in details_df.")
            raise ValueError(f"Missing column '{col}' in details_df")

    if 'remnant_id' not in current_materials_df.columns:
        current_materials_df['remnant_id'] = None # Ensure 'remnant_id' column exists
        logger.info("Added missing 'remnant_id' column to materials DataFrame, initialized to None.")

    # --- Process Each Material Combination ---
    unique_combinations = details_df[['thickness_mm', 'material']].drop_duplicates()
    logger.info(f"Found {len(unique_combinations)} unique material/thickness combinations in details.")

    for _, combination_row in unique_combinations.iterrows():
        thickness = combination_row['thickness_mm']
        material_code = combination_row['material'] # Renamed for clarity
        material_key = f"{thickness}_{material_code}" if material_code != 'S' else str(thickness)
        logger.info(f"\nProcessing material combination: Thickness={thickness}, Material='{material_code}' (Key: {material_key})")

        # Filter details and materials for the current combination
        details_df_mask = (details_df['thickness_mm'] == thickness) & (details_df['material'] == material_code)
        details_for_current_material = details_df[details_df_mask].copy()
        if details_for_current_material.empty:
            logger.info(f"No details found for material key {material_key}.")
            continue

        sheets_df_mask = (current_materials_df['thickness_mm'] == thickness) & \
                         (current_materials_df['material'] == material_code)
        sheets_for_current_material = current_materials_df[sheets_df_mask].copy()
        if sheets_for_current_material.empty:
            logger.info(f"No material sheets/remnants found for material key {material_key}.")
            continue

        # 1. Prepare Details for Packing (add kerf, create unique IDs)
        rects_for_current_material = _prepare_details_for_packing(details_for_current_material, kerf)
        if not rects_for_current_material:
            logger.info(f"No valid details to pack for material key {material_key} after preparation.")
            continue
        rects_for_current_material = hybrid_sort(rects_for_current_material) # Sort details for packing efficiency

        # 2. Prepare Material Sheets (separate remnants and full sheets, calculate packing dimensions)
        material_remnants, material_remnants_by_id, material_full_sheets = \
            _prepare_materials(sheets_for_current_material, margin)

        if not material_remnants and not material_full_sheets:
            logger.info(f"No remnants or full sheets available for material key {material_key}.")
            continue

        layouts_for_material = [] # Stores ("type", id, packer_instance) for this material

        # 3. Pack into Remnants (Phase 1)
        packed_remnant_layouts, used_remnant_ids = _pack_into_remnants(
            material_remnants, rects_for_current_material, margin
        )
        layouts_for_material.extend(packed_remnant_layouts)

        # Collect IDs of details packed in remnants to avoid repacking them into full sheets
        detail_ids_packed_in_remnants = set()
        for _, _, remnant_packer_instance in packed_remnant_layouts:
            if len(remnant_packer_instance) > 0 and remnant_packer_instance[0]: # Check if packer has a bin and items
                for rect in remnant_packer_instance[0]: # Access items in the first (and only) bin
                    detail_ids_packed_in_remnants.add(rect.rid)
        logger.info(f"After remnant packing for {material_key}: {len(detail_ids_packed_in_remnants)} detail instances packed.")

        # 4. Pack into Full Sheets (Phase 2)
        packed_sheet_layouts, used_full_sheets_count = _pack_into_full_sheets(
            material_full_sheets,
            rects_for_current_material, # Pass the original full list of rects for this material
            detail_ids_packed_in_remnants,  # Pass the set of IDs already packed in remnants
            margin
        )
        layouts_for_material.extend(packed_sheet_layouts)
        total_used_sheets_overall += used_full_sheets_count

        # 5. Process Layouts: Generate DXF files and create a final packer for the material
        if not layouts_for_material:
            logger.info(f"No layouts (packed remnants or sheets) were created for material key {material_key}.")
            packers_by_material[material_key] = newPacker() # Store an empty packer if no layouts
            continue

        final_packer_for_material, total_layout_count = _generate_dxf_files_for_layouts(
            layouts_for_material, details_for_current_material,
            material_full_sheets, material_remnants_by_id,
            thickness, material_code, margin, kerf, total_layout_count
        )
        packers_by_material[material_key] = final_packer_for_material

        # --- Update Material Table (current_materials_df) ---
        # Remove used remnants
        if used_remnant_ids:
            logger.info(f"Removing {len(used_remnant_ids)} used remnant types/quantities for material {material_key}.")
            initial_remnant_rows = len(current_materials_df[
                (current_materials_df['is_remnant'] == True) &
                (current_materials_df['thickness_mm'] == thickness) &
                (current_materials_df['material'] == material_code)
            ])

            # This logic needs to be careful if remnant_ids are not unique per instance in original table
            # Assuming RemnantsManager handles decrementing quantities or removing rows appropriately.
            # For now, a simplified removal based on ID:
            if 'remnant_id' in current_materials_df.columns:
                # This mask identifies specific remnant entries (by ID, thickness, material) to be removed/adjusted.
                # A more robust solution might involve RemnantsManager to decrement quantities.
                delete_mask = (current_materials_df['is_remnant'] == True) & \
                              (current_materials_df['remnant_id'].isin(list(used_remnant_ids))) & \
                              (current_materials_df['thickness_mm'] == thickness) & \
                              (current_materials_df['material'] == material_code)
                current_materials_df = current_materials_df[~delete_mask] # Keep rows NOT matching the mask

                final_remnant_rows = len(current_materials_df[
                    (current_materials_df['is_remnant'] == True) &
                    (current_materials_df['thickness_mm'] == thickness) &
                    (current_materials_df['material'] == material_code)
                ])
                logger.info(f"Removed {initial_remnant_rows - final_remnant_rows} remnant entries for material {material_key}.")
            else: # Should not happen due to earlier check, but good for safety
                logger.warning("Cannot remove used remnants: 'remnant_id' column missing.")

        # Add new remnants generated from packed sheets (using RemnantsManager)
        # Find a standard sheet definition from the *original* materials_df to get its dimensions
        # This is used by RemnantsManager to know the properties of the sheet from which remnants are cut.
        std_sheet_mask = (
            (materials_df['thickness_mm'] == thickness) &
            (materials_df['material'] == material_code) &
            (materials_df['is_remnant'] == False)
        )
        std_sheet_properties = materials_df[std_sheet_mask].iloc[0] if std_sheet_mask.any() else None

        if std_sheet_properties is not None:
            original_sheet_length = std_sheet_properties['sheet_length_mm']
            original_sheet_width = std_sheet_properties['sheet_width_mm']
            current_materials_df = remnants_manager.update_material_table(
                materials_df_to_update=current_materials_df,
                packer_with_new_remnants=final_packer_for_material,
                material_thickness=thickness,
                material_code=material_code,
                num_sheets_processed=used_full_sheets_count, # Number of full sheets that might have generated these remnants
                original_sheet_length=original_sheet_length,
                original_sheet_width=original_sheet_width
            )
        else:
            logger.warning(
                f"No standard sheet definition found for material {material_key}. "
                "Cannot accurately update new remnants based on original sheet dimensions. "
                "Updating remnants without original sheet context."
            )
            current_materials_df = remnants_manager.update_material_table(
                materials_df_to_update=current_materials_df,
                packer_with_new_remnants=final_packer_for_material,
                material_thickness=thickness,
                material_code=material_code,
                num_sheets_processed=used_full_sheets_count
                # sheet_length and sheet_width omitted, RemnantsManager should handle this case
            )

    # --- Final Operations ---
    if 'remnant_id' not in current_materials_df.columns: # Should be redundant given earlier checks
        current_materials_df['remnant_id'] = None
        logger.warning("Final check: 'remnant_id' column was missing and has been added before saving.")

    final_remnant_count = sum(1 for _, r_row in current_materials_df.iterrows() if r_row.get('is_remnant', False))
    logger.info(f"Total remnants in the updated materials table: {final_remnant_count}")

    # Save the updated materials table (with used remnants removed and new ones added)
    remnants_manager.save_material_table(current_materials_df, "updated_materials.csv")

    logger.info(
        f"Packing process completed. "
        f"Total full sheets used: {total_used_sheets_overall}, "
        f"Total DXF layouts generated: {total_layout_count}."
    )
    logger.info(f"Final count of all remnant entries in 'updated_materials.csv': {final_remnant_count}.")

    return packers_by_material, total_used_sheets_overall, total_layout_count
