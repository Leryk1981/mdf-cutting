import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pandas as pd
from fastapi.encoders import jsonable_encoder

from packer.layout_review import (
    LayoutSnapshot,
    Placement,
    refresh_guillotine_cuts,
)
from packer.web_app import (
    ApprovalRequest,
    MoveRequest,
    WebReviewSession,
    approve,
    move,
    store,
)


class WebAppTests(unittest.TestCase):
    def make_session(self, directory):
        details = pd.DataFrame([{
            "part_id": "1",
            "order_id": "ORDER-1",
            "length_mm": 996,
            "width_mm": 196,
            "quantity": 1,
            "material": "S",
            "thickness_mm": 16.0,
            "milling_type": "",
            "bevel_type": "",
            "bevel_offset_mm": 0,
            "f_long": 0,
            "f_short": 0,
        }])
        materials = pd.DataFrame([{
            "material": "S",
            "thickness_mm": 16.0,
            "sheet_width_mm": 1012,
            "sheet_length_mm": 1212,
            "total_quantity": 2,
            "is_remnant": False,
            "remnant_id": None,
        }])
        layouts = refresh_guillotine_cuts((LayoutSnapshot(
            "16:sheet:0",
            1200,
            1000,
            (Placement(
                (16, 0), 0, 0, 1000, 200,
                source_index=0, material_key=16,
            ),),
            material_key=16,
            container_type="sheet",
            container_id=0,
            output_file=str(Path(directory) / "sheet_16mm_0.dxf"),
            thickness=16.0,
            material="S",
        ),))
        session_id = uuid4().hex
        session = WebReviewSession(
            session_id=session_id,
            packing_result=SimpleNamespace(total_used_sheets=1),
            details_df=details,
            materials_df=materials,
            output_dir=Path(directory),
            pending_materials_path=Path(directory) / "updated_materials.pending.csv",
            published_materials_path=Path(directory) / "updated_materials.csv",
            margin=6,
            kerf=4,
            original_layouts=layouts,
            layouts=layouts,
        )
        store.add(session)
        return session

    def test_move_updates_svg_payload_cut_and_supports_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            session = self.make_session(directory)

            payload = move(session.session_id, MoveRequest(
                placement_id="p1",
                target_layout_id="16:sheet:0",
                x=0,
                y=100,
            ))

            self.assertTrue(payload["summary"]["dirty"])
            self.assertEqual(payload["summary"]["undo_count"], 1)
            self.assertEqual(payload["layouts"][0]["cut"]["position"], 300)
            self.assertEqual(payload["layouts"][0]["placements"][0]["y"], 100)
            self.assertIsInstance(jsonable_encoder(payload), dict)

    def test_web_move_applies_operator_snap_tolerance(self):
        with tempfile.TemporaryDirectory() as directory:
            session = self.make_session(directory)

            payload = move(session.session_id, MoveRequest(
                placement_id="p1",
                target_layout_id="16:sheet:0",
                x=4,
                y=100,
                snap_tolerance=5,
            ))

            self.assertEqual(payload["layouts"][0]["placements"][0]["x"], 0)
            self.assertTrue(payload["move"]["snapped"])

    def test_original_approval_publishes_pending_warehouse(self):
        with tempfile.TemporaryDirectory() as directory:
            session = self.make_session(directory)
            session.pending_materials_path.write_text(
                "material;is_remnant\nS;False\n", encoding="utf-8")

            payload = approve(
                session.session_id, ApprovalRequest(variant="original"))

            self.assertTrue(payload["approved"])
            self.assertFalse(session.pending_materials_path.exists())
            self.assertTrue(session.published_materials_path.exists())

    def test_browser_editor_uses_svg_and_crisp_non_scaling_lines(self):
        root = Path(__file__).resolve().parents[1] / "web"
        html = (root / "index.html").read_text(encoding="utf-8")
        css = (root / "styles.css").read_text(encoding="utf-8")
        script = (root / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="layout-svg"', html)
        self.assertNotIn('id="pattern-dir"', html)
        self.assertIn('data-browse="details"', html)
        self.assertIn('data-browse="output"', html)
        self.assertIn("vector-effect: non-scaling-stroke", css)
        self.assertIn("shape-rendering: crispEdges", css)
        self.assertIn(".setup.collapsed #run-form", css)
        self.assertIn("pointermove", script)
        self.assertIn("previewSnap", script)
        self.assertIn("Прилипло", script)
        self.assertIn('sessionAction("cut"', script)
        self.assertIn('?session=${session.session_id}', script)


if __name__ == "__main__":
    unittest.main()
