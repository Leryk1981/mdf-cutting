"""Generate isolated DXF and material-ledger outputs for a review proposal."""

from pathlib import Path

from .dxf_generator import (
    add_detail_to_sheet,
    add_details_list,
    add_layout_filename_title,
    add_sheet_outline,
    create_new_dxf,
)
from .remnants import RemnantsManager


def calculate_layout_remnants(layout, minimum_width=60, minimum_length=1000):
    """Calculate non-overlapping usable remnants from one layout snapshot."""
    x_edges = sorted({
        0,
        layout.width,
        *(edge for item in layout.placements
          for edge in (item.x, item.x + item.width)),
    })
    y_edges = sorted({
        0,
        layout.height,
        *(edge for item in layout.placements
          for edge in (item.y, item.y + item.height)),
    })
    free_spaces = []
    for x0, x1 in zip(x_edges, x_edges[1:]):
        for y0, y1 in zip(y_edges, y_edges[1:]):
            occupied = any(
                item.x < x1 and item.x + item.width > x0
                and item.y < y1 and item.y + item.height > y0
                for item in layout.placements
            )
            if not occupied:
                free_spaces.append((x0, y0, x1 - x0, y1 - y0))

    free_spaces = RemnantsManager.merge_adjacent_free_spaces(free_spaces)
    remnants = []
    for _x, _y, width, height in free_spaces:
        if min(width, height) < minimum_width:
            continue
        if max(width, height) < minimum_length:
            continue
        remnants.append((max(width, height), min(width, height)))
    return remnants


def build_material_ledger(materials_df, layouts, margin, kerf):
    """Reconcile inventory against the exact containers in a proposal."""
    manager = RemnantsManager(margin=margin, kerf=kerf)
    updated = materials_df.copy()
    grouped_layouts = {}
    for layout in layouts:
        key = (layout.thickness, layout.material)
        if layout.thickness is None or not layout.material:
            raise ValueError(f"У карты {layout.layout_id} нет данных материала")
        grouped_layouts.setdefault(key, []).append(layout)

    for (thickness, material), material_layouts in grouped_layouts.items():
        consumed_remnants = {
            layout.container_id
            for layout in material_layouts
            if layout.container_type == "remnant"
        }
        if consumed_remnants:
            mask = (
                (updated["thickness_mm"] == thickness)
                & (updated["material"] == material)
                & (updated["is_remnant"] == True)
                & (updated["remnant_id"].isin(consumed_remnants))
            )
            updated = updated.loc[~mask].copy()

        used_sheets = sum(
            layout.container_type == "sheet" for layout in material_layouts)
        generated_remnants = [
            remnant
            for layout in material_layouts
            for remnant in calculate_layout_remnants(
                layout,
                manager.min_remnant_width,
                manager.min_remnant_length,
            )
        ]
        whole_sheet_mask = (
            (updated["thickness_mm"] == thickness)
            & (updated["material"] == material)
            & (updated["is_remnant"] == False)
        )
        whole_sheets = updated.loc[whole_sheet_mask]
        if not whole_sheets.empty:
            sheet_length = float(whole_sheets.iloc[0]["sheet_length_mm"])
            sheet_width = float(whole_sheets.iloc[0]["sheet_width_mm"])
        else:
            first_layout = material_layouts[0]
            sheet_length = first_layout.width + 2 * margin
            sheet_width = first_layout.height + 2 * margin

        updated = manager.update_material_table(
            updated,
            packer=None,
            thickness=thickness,
            material=material,
            used_sheets=used_sheets,
            sheet_length=sheet_length,
            sheet_width=sheet_width,
            remnants=generated_remnants,
        )
    return updated


def render_candidate_dxf(layouts, details_df, output_dir, margin, kerf):
    """Render proposal layouts into a separate review directory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written_paths = []

    for layout in layouts:
        material_details = details_df[
            (details_df["thickness_mm"] == layout.thickness)
            & (details_df["material"] == layout.material)
        ].reset_index(drop=True)
        if material_details.empty:
            raise ValueError(f"Не найдены детали для карты {layout.layout_id}")

        filename = Path(layout.output_file).name
        if not filename:
            raise ValueError(f"У карты {layout.layout_id} нет имени DXF")
        original_length = layout.width + 2 * margin
        original_width = layout.height + 2 * margin
        doc, modelspace = create_new_dxf()
        add_sheet_outline(
            modelspace, original_length, original_width, margin)
        details_list = []

        for placement in layout.placements:
            if placement.source_index is None:
                raise ValueError(
                    f"У детали {placement.placement_id} нет ссылки на источник")
            detail = material_details.iloc[placement.source_index]
            detail_rect = {
                "x": placement.x + margin,
                "y": placement.y + margin,
                "width": placement.width - kerf,
                "height": placement.height - kerf,
                "rotated": placement.rotated,
            }
            detail_info = add_detail_to_sheet(
                modelspace, detail, detail_rect, kerf)
            if detail_info:
                details_list.append(detail_info)

        add_layout_filename_title(
            modelspace, original_length, original_width, filename)
        add_details_list(modelspace, original_width, details_list)
        output_path = output_dir / filename
        doc.saveas(output_path)
        written_paths.append(output_path)

    return tuple(written_paths)


def write_candidate_outputs(
        layouts, details_df, materials_df, output_dir, margin, kerf):
    """Write a complete, isolated proposal for visual and ledger review."""
    output_dir = Path(output_dir)
    dxf_paths = render_candidate_dxf(
        layouts, details_df, output_dir, margin, kerf)
    materials = build_material_ledger(
        materials_df, layouts, margin, kerf)
    materials_path = output_dir / "updated_materials.pending.csv"
    RemnantsManager(margin=margin, kerf=kerf).save_material_table(
        materials, materials_path)
    return dxf_paths, materials_path
