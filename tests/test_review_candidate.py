import tempfile
import unittest
from pathlib import Path

import pandas as pd

from packer.dxf_generator import add_guillotine_plan, create_new_dxf
from packer.layout_review import (
    LayoutSnapshot,
    Placement,
    refresh_guillotine_cut,
    toggle_guillotine_cut,
)
from packer.review_candidate import (
    build_material_ledger,
    publish_candidate_outputs,
    render_candidate_dxf,
)


class ReviewCandidateTests(unittest.TestCase):
    @staticmethod
    def stepped_layout():
        return refresh_guillotine_cut(LayoutSnapshot(
            "16:sheet:3", 2788, 2058,
            (
                Placement("93", 0, 0, 820, 1987),
                Placement("2", 820, 0, 1952, 833),
                Placement("57", 820, 833, 1954, 819),
                Placement("14", 0, 1987, 2154, 49),
            ),
            material_key=16,
            container_type="sheet",
            container_id=3,
            thickness=16,
            material="S",
        ))

    def test_candidate_ledger_uses_operator_selected_guillotine_cut(self):
        materials = pd.DataFrame([{
            "material": "S",
            "thickness_mm": 16,
            "sheet_length_mm": 1212,
            "sheet_width_mm": 1012,
            "total_quantity": 2,
            "is_remnant": False,
            "remnant_id": None,
        }])
        layout = refresh_guillotine_cut(LayoutSnapshot(
            "16:sheet:0", 1200, 1000,
            (Placement("A", 0, 0, 1000, 200, material_key=16),),
            material_key=16,
            container_type="sheet",
            container_id=0,
            thickness=16,
            material="S",
        ))
        layout = toggle_guillotine_cut((layout,), layout.layout_id)[0]

        result = build_material_ledger(
            materials, (layout,), margin=6, kerf=4)

        remnants = result[result["is_remnant"] == True]
        self.assertEqual(len(remnants), 2)
        self.assertEqual(
            set(zip(
                remnants["sheet_length_mm"],
                remnants["sheet_width_mm"],
            )),
            {(1000.0, 800.0), (1000.0, 200.0)},
        )

    def test_three_cut_plan_drives_ledger_and_dxf(self):
        materials = pd.DataFrame([{
            "material": "S",
            "thickness_mm": 16,
            "sheet_length_mm": 2800,
            "sheet_width_mm": 2070,
            "total_quantity": 2,
            "is_remnant": False,
            "remnant_id": None,
        }])
        layout = self.stepped_layout()

        ledger = build_material_ledger(
            materials, (layout,), margin=6, kerf=4)
        remnants = ledger[ledger["is_remnant"] == True]
        self.assertEqual(len(remnants), 1)
        self.assertEqual(
            (remnants.iloc[0]["sheet_length_mm"],
             remnants.iloc[0]["sheet_width_mm"]),
            (1968.0, 335.0),
        )

        _document, modelspace = create_new_dxf()
        add_guillotine_plan(modelspace, layout.cut_plan, margin=6)
        self.assertEqual(
            len(modelspace.query('LINE[layer=="guillotine_cut"]')), 3)
        self.assertEqual(
            len(modelspace.query('TEXT[layer=="guillotine_cut"]')), 3)

    def test_publish_candidate_replaces_only_reviewed_outputs_and_keeps_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_dir = root / "candidate"
            candidate_dir.mkdir()
            first = root / "sheet_1.dxf"
            freed = root / "sheet_2.dxf"
            pending = root / "updated_materials.pending.csv"
            first.write_text("original one", encoding="utf-8")
            freed.write_text("original two", encoding="utf-8")
            pending.write_text("original ledger", encoding="utf-8")
            (candidate_dir / first.name).write_text(
                "candidate one", encoding="utf-8")
            candidate_ledger = candidate_dir / pending.name
            candidate_ledger.write_text("candidate ledger", encoding="utf-8")
            original_layouts = (
                LayoutSnapshot("one", 1, 1, (), output_file=str(first)),
                LayoutSnapshot("two", 1, 1, (), output_file=str(freed)),
            )
            candidate_layouts = (
                LayoutSnapshot("one", 1, 1, (), output_file=str(first)),
            )

            backup_dir = publish_candidate_outputs(
                original_layouts,
                candidate_layouts,
                candidate_dir,
                candidate_ledger,
                pending,
            )

            self.assertEqual(first.read_text(encoding="utf-8"), "candidate one")
            self.assertFalse(freed.exists())
            self.assertEqual(pending.read_text(encoding="utf-8"), "candidate ledger")
            self.assertEqual(
                (backup_dir / first.name).read_text(encoding="utf-8"),
                "original one",
            )
            self.assertEqual(
                (backup_dir / freed.name).read_text(encoding="utf-8"),
                "original two",
            )

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
            import ezdxf
            document = ezdxf.readfile(paths[0])
            cut_lines = document.modelspace().query(
                'LINE[layer=="guillotine_cut"]')
            self.assertEqual(len(cut_lines), 1)
            self.assertEqual(cut_lines[0].dxf.linetype, "DASHED")


if __name__ == "__main__":
    unittest.main()
