import unittest

import pandas as pd

from packer.packing import PackingRunResult, build_rectangles_to_pack


class PackingPreparationTests(unittest.TestCase):
    def test_run_result_keeps_legacy_tuple_unpacking(self):
        result = PackingRunResult(
            packers_by_material={"16_S": object()},
            total_used_sheets=2,
            layout_count=3,
            layouts=(),
        )

        packers, used_sheets, layout_count = result

        self.assertEqual(set(packers), {"16_S"})
        self.assertEqual(used_sheets, 2)
        self.assertEqual(layout_count, 3)

    def test_quantity_expands_to_unique_rectangle_ids(self):
        details = pd.DataFrame([
            {"part_id": "A", "length_mm": 100, "width_mm": 50, "quantity": 3},
            {"part_id": "B", "length_mm": 80, "width_mm": 40, "quantity": 2},
        ])

        rectangles, detail_indices = build_rectangles_to_pack(details, kerf=4)

        self.assertEqual(len(rectangles), 5)
        self.assertEqual([rectangle[2] for rectangle in rectangles], [0, 1, 2, 3, 4])
        self.assertEqual(detail_indices, {0: 0, 1: 0, 2: 0, 3: 1, 4: 1})
        self.assertEqual(rectangles[0][:2], (104, 54))
