import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "download_models.py"


def load_downloader():
    spec = importlib.util.spec_from_file_location("download_models", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DownloaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.downloader = load_downloader()

    def test_manifest_order_and_total(self):
        models = self.downloader.MODELS
        self.assertEqual(5, len(models))
        self.assertEqual(
            "10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors",
            models[0].filename,
        )
        self.assertEqual(
            "10Eros_Max_h3_hybrid_beta5_int8.safetensors",
            models[-1].filename,
        )
        self.assertEqual(61_044_291_471, sum(model.size_bytes for model in models))
        self.assertEqual(len(models), len({model.destination for model in models}))

    def test_download_installs_verified_file(self):
        payload = b"verified model payload"
        model = self._model(payload)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_hub = self._fake_hub(payload)
            with mock.patch.dict(sys.modules, {"huggingface_hub": fake_hub}):
                self.downloader.download_one(root, root / "staging", model, "secret")

            destination = self.downloader.target_path(root, model)
            self.assertEqual(payload, destination.read_bytes())
            self.assertTrue(self.downloader.verified(destination, model))

    def test_bad_hash_is_removed(self):
        expected = b"expected"
        model = self._model(expected)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_hub = self._fake_hub(b"corrupt")
            with mock.patch.dict(sys.modules, {"huggingface_hub": fake_hub}):
                with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                    self.downloader.download_one(root, root / "staging", model, "secret")

            self.assertFalse(self.downloader.target_path(root, model).exists())
            self.assertFalse(any((root / "staging").rglob("payload.bin")))

    def test_missing_authorization_writes_failed_status(self):
        payload = b"small"
        model = self._model(payload)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            status = root / "status.json"
            argv = [
                str(MODULE_PATH),
                "--comfy-root",
                str(root),
                "--status-file",
                str(status),
            ]
            with (
                mock.patch.object(self.downloader, "MODELS", (model,)),
                mock.patch.object(sys, "argv", argv),
                mock.patch.dict(os.environ, {}, clear=True),
            ):
                with self.assertRaisesRegex(RuntimeError, "MINIMAX_H3_AUTHORIZED"):
                    self.downloader.main()

            self.assertEqual("failed", json.loads(status.read_text())["state"])

    def test_insufficient_storage_fails_before_download(self):
        payload = b"small"
        model = self._model(payload)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            status = root / "status.json"
            argv = [
                str(MODULE_PATH),
                "--comfy-root",
                str(root),
                "--status-file",
                str(status),
            ]
            environment = {"MINIMAX_H3_AUTHORIZED": "1", "HF_TOKEN": "secret"}
            with (
                mock.patch.object(self.downloader, "MODELS", (model,)),
                mock.patch.object(sys, "argv", argv),
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(
                    self.downloader.shutil,
                    "disk_usage",
                    return_value=types.SimpleNamespace(free=0),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "Not enough free persistent storage"):
                    self.downloader.main()

            self.assertEqual("failed", json.loads(status.read_text())["state"])

    def _model(self, payload):
        return self.downloader.ModelFile(
            repo_id="example/repo",
            revision="revision",
            filename="payload.bin",
            destination="diffusion_models/payload.bin",
            sha256=hashlib.sha256(payload).hexdigest(),
            size_bytes=len(payload),
        )

    @staticmethod
    def _fake_hub(payload):
        module = types.ModuleType("huggingface_hub")

        def hf_hub_download(**kwargs):
            destination = Path(kwargs["local_dir"]) / kwargs["filename"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
            return str(destination)

        module.hf_hub_download = hf_hub_download
        return module


if __name__ == "__main__":
    unittest.main()
