import tempfile
import unittest
from pathlib import Path

from packer.operator_review import count_material_remnants, finalize_materials_draft


class OperatorReviewTests(unittest.TestCase):
    def test_remnant_count_is_read_from_calculated_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            draft_path = Path(directory) / "updated_materials.pending.csv"
            draft_path.write_text(
                "material;is_remnant;remnant_id\n"
                "S;False;\n"
                "S;True;R-1\n"
                "S;true;R-2\n",
                encoding="utf-8",
            )

            self.assertEqual(count_material_remnants(draft_path), 2)

    def test_rejected_draft_does_not_change_published_materials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft_path = root / "updated_materials.pending.csv"
            published_path = root / "updated_materials.csv"
            draft_path.write_text("new inventory", encoding="utf-8")
            published_path.write_text("current inventory", encoding="utf-8")

            result_path = finalize_materials_draft(
                draft_path, published_path, approved=False)

            self.assertEqual(result_path, draft_path)
            self.assertEqual(
                published_path.read_text(encoding="utf-8"), "current inventory")
            self.assertEqual(
                draft_path.read_text(encoding="utf-8"), "new inventory")

    def test_approved_draft_atomically_replaces_published_materials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft_path = root / "updated_materials.pending.csv"
            published_path = root / "updated_materials.csv"
            draft_path.write_text("new inventory", encoding="utf-8")
            published_path.write_text("current inventory", encoding="utf-8")

            result_path = finalize_materials_draft(
                draft_path, published_path, approved=True)

            self.assertEqual(result_path, published_path)
            self.assertEqual(
                published_path.read_text(encoding="utf-8"), "new inventory")
            self.assertFalse(draft_path.exists())

    def test_missing_draft_cannot_be_approved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            with self.assertRaises(FileNotFoundError):
                finalize_materials_draft(
                    root / "missing.pending.csv",
                    root / "updated_materials.csv",
                    approved=True,
                )


if __name__ == "__main__":
    unittest.main()
