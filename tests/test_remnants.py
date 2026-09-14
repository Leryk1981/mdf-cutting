import unittest

import pandas as pd
from rectpack import MaxRectsBssf, newPacker

from packer.remnants import RemnantsManager


class RemnantsManagerTests(unittest.TestCase):
    def test_leftovers_are_disjoint_and_conserve_free_area(self):
        packer = newPacker(rotation=False, pack_algo=MaxRectsBssf)
        packer.add_bin(1000, 1000)
        packer.add_rect(600, 400, 1)
        packer.add_rect(300, 500, 2)
        packer.pack()

        manager = RemnantsManager()
        manager.min_remnant_width = 1
        manager.min_remnant_length = 1
        leftovers = manager.calculate_remnants(packer, 1012, 1012, 6)

        placed_area = sum(rect.width * rect.height for rect in packer[0])
        self.assertEqual(sum(width * height for width, height in leftovers), 1_000_000 - placed_area)

    def test_update_persists_usable_leftovers_with_identifiers(self):
        materials = pd.DataFrame([{
            "material": "S", "thickness_mm": 16, "sheet_width_mm": 2070,
            "sheet_length_mm": 2800, "total_quantity": 2,
            "is_remnant": False, "remnant_id": None,
        }])

        updated = RemnantsManager().update_material_table(
            materials, None, 16, "S", used_sheets=1,
            remnants=[(1200, 200)],
        )

        full_sheet = updated[updated["is_remnant"] == False].iloc[0]
        remnants = updated[updated["is_remnant"] == True]
        self.assertEqual(full_sheet["total_quantity"], 1)
        self.assertEqual(len(remnants), 1)
        self.assertTrue(remnants.iloc[0]["remnant_id"].startswith("auto-"))
