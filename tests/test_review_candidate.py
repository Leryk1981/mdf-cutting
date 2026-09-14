import tempfile
import unittest
from pathlib import Path

import pandas as pd

from packer.layout_review import LayoutSnapshot, Placement
from packer.review_candidate import (
    build_material_ledger,
    render_candidate_dxf,
)


class ReviewCandidateTests(unittest.TestCase):
    def test_candidate_ledger_consumes_exact_selected_containers(self):
        materials = pd.DataFrame([
            {
                "material": "S",
                "thickness_mm": 16,
                "sheet_length_mm": 1200,
                "sheet_width_mm": 1000,
                "total_quantity": 2,
                "is_remnant": False,
                "remnant_id": None,
            },
            {
                "material": "S",
                "thickness_mm": 16,
                "sheet_length_mm": 1200,
                "sheet_width_mm": 500,
                "total_quantity": 1,
                "is_remnant": True,
                "remnant_id": "R-1",
            },
        ])
        layouts = (
            LayoutSnapshot(
                "16:remnant:R-1", 1188, 488,
                (Placement("A", 0, 0, 1188, 488, material_key=16),),
                material_key=16,
                container_type="remnant",
                container_id="R-1",
                thickness=16,
                material="S",
            ),
            LayoutSnapshot(
                "16:sheet:0", 1188, 988,
                (Placement("B", 0, 0, 1188, 988, material_key=16),),
                material_key=16,
                container_type="sheet",
                container_id=0,
                thickness=16,
                material="S",
            ),
        )

        result = build_material_ledger(materials, layouts, margin=6, kerf=4)

        whole = result[result["is_remnant"] == False]
        remnants = result[result["is_remnant"] == True]
        self.assertEqual(int(whole["total_quantity"].sum()), 1)
        self.assertTrue(remnants.empty)

    def test_candidate_renderer_writes_separate_dxf(self):
        details = pd.DataFrame([{
            "part_id": "1",
            "order_id": "O-1",
            "length_mm": 100,
            "width_mm": 50,
            "quantity": 1,
            "thickness_mm": 16,
            "material": "S",
            "milling_type": "",
            "bevel_type": "",
            "bevel_offset_mm": 0,
            "f_long": 0,
            "f_short": 0,
        }])
        layout = LayoutSnapshot(
            "16:sheet:0",
            1188,
            988,
            (Placement(
                ("16", 0), 0, 0, 104, 54,
                source_index=0, material_key=16,
            ),),
            material_key=16,
            container_type="sheet",
            container_id=0,
            output_file="sheet_16mm_0.dxf",
            thickness=16,
            material="S",
        )

        with tempfile.TemporaryDirectory() as directory:
            paths = render_candidate_dxf(
                (layout,), details, directory, margin=6, kerf=4)

            self.assertEqual(len(paths), 1)
            self.assertEqual(paths[0].name, "sheet_16mm_0.dxf")
            self.assertGreater(paths[0].stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
