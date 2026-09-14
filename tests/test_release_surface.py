import unittest
from pathlib import Path

from packer.web_app import config


class ReleaseSurfaceTests(unittest.TestCase):
    def test_browser_is_the_only_application_launch_surface(self):
        root = Path(__file__).resolve().parents[1]
        main = (root / "main.py").read_text(encoding="utf-8")

        self.assertIn("from web_app import app", main)
        self.assertIn("MDF_CUTTING_PORT", main)
        self.assertIn("log_config=None", main)
        self.assertNotIn("--legacy-tk", main)
        self.assertFalse((root / "gui.py").exists())
        self.assertFalse((root / "review_dialog.py").exists())
        self.assertTrue((root / "scripts" / "build_windows.ps1").is_file())
        self.assertTrue((root / "installer" / "MdfCutting.iss").is_file())

    def test_release_does_not_suggest_production_input_files(self):
        defaults = config()

        self.assertEqual(defaults["details_path"], "")
        self.assertEqual(defaults["materials_path"], "")
        self.assertEqual(defaults["output_dir"], "")


if __name__ == "__main__":
    unittest.main()
