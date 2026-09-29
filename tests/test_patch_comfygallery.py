import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "patch_comfygallery.py"


def load_patcher():
    spec = importlib.util.spec_from_file_location("patch_comfygallery", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GalleryPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patcher = load_patcher()

    def test_patch_is_applied_and_idempotent(self):
        source = "before\n" + self.patcher.ANCHOR + "  launchPending = true;\nafter\n"
        with tempfile.TemporaryDirectory() as temporary:
            javascript = Path(temporary) / "button.js"
            javascript.write_text(source, encoding="utf-8")
            argv = [str(MODULE_PATH), str(javascript)]

            with mock.patch.object(sys, "argv", argv):
                self.assertEqual(0, self.patcher.main())
                first = javascript.read_text(encoding="utf-8")
                self.assertIn(self.patcher.MARKER, first)
                self.assertIn("-8190.proxy.runpod.net", first)
                self.assertEqual(0, self.patcher.main())
                self.assertEqual(first, javascript.read_text(encoding="utf-8"))

    def test_upstream_change_fails_loudly(self):
        with tempfile.TemporaryDirectory() as temporary:
            javascript = Path(temporary) / "button.js"
            javascript.write_text("changed upstream", encoding="utf-8")
            argv = [str(MODULE_PATH), str(javascript)]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaisesRegex(RuntimeError, "changed upstream"):
                    self.patcher.main()


if __name__ == "__main__":
    unittest.main()
