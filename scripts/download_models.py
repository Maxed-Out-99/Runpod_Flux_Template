#!/usr/bin/env python3
"""Download and verify the MiniMax H3 Turbo and non-Turbo model stack."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelFile:
    repo_id: str
    revision: str
    filename: str
    destination: str
    sha256: str
    size_bytes: int


MODELS = (
    ModelFile(
        repo_id="TenStrip/10Eros-Max",
        revision="b0070d3c9fb8b25c4b954aeb740e2f80924040df",
        filename="10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors",
        destination="diffusion_models/10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors",
        sha256="4dd965496e5b1b83cd13c65cbe7a535b8a4d94ae768a7646b4e336d52c4781cf",
        size_bytes=20_970_414_464,
    ),
    ModelFile(
        repo_id="Comfy-Org/MiniMax-H3",
        revision="3f57e8291d2ef846f9a074b1b76d2767db434abe",
        filename="text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
        destination="text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
        sha256="35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6",
        size_bytes=15_687_142_551,
    ),
    ModelFile(
        repo_id="Comfy-Org/MiniMax-H3",
        revision="7a2065e37f5ff9d3c4e605f164d4cac388eff8e8",
        filename="vae/minimax_h3_video_vae_int8_convrot.safetensors",
        destination="vae/minimax_h3_video_vae_int8_convrot.safetensors",
        sha256="52a2c8c73583c86e4f41cdcce3a6ad0ea562987bc0bf3d60a0cef5f5c8e60c0e",
        size_bytes=2_811_065_184,
    ),
    ModelFile(
        repo_id="Comfy-Org/MiniMax-H3",
        revision="3f57e8291d2ef846f9a074b1b76d2767db434abe",
        filename="vae/minimax_h3_audio_vae_fp32.safetensors",
        destination="vae/minimax_h3_audio_vae_fp32.safetensors",
        sha256="8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48",
        size_bytes=605_254_808,
    ),
    ModelFile(
        repo_id="Comfy-Org/BiRefNet",
        revision="35767b272f2846752a3aee1259abdd4586f735c8",
        filename="background_removal/birefnet.safetensors",
        destination="background_removal/birefnet.safetensors",
        sha256="9ab37426bf4de0567af6b5d21b16151357149139362e6e8992021b8ce356a154",
        size_bytes=444_473_596,
    ),
    ModelFile(
        repo_id="TenStrip/10Eros-Max",
        revision="b0070d3c9fb8b25c4b954aeb740e2f80924040df",
        filename="10Eros_Max_h3_hybrid_beta5_int8.safetensors",
        destination="diffusion_models/10Eros_Max_h3_hybrid_beta5_int8.safetensors",
        sha256="488e0d51fad9fd6b277b6ebfbe46b3fd44374ff7baa1e3c9dfce58d3a1e5b33c",
        size_bytes=20_970_414_464,
    ),
)

DISK_SAFETY_MARGIN_BYTES = 5 * 1024**3


def sha256_file(path: Path, block_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def write_status(path: Path | None, state: str, **details: object) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    payload = {"state": state, "updated_at": int(time.time()), **details}
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def target_path(comfy_root: Path, model: ModelFile) -> Path:
    return comfy_root / "models" / model.destination


def verified(path: Path, model: ModelFile) -> bool:
    return (
        path.is_file()
        and path.stat().st_size == model.size_bytes
        and sha256_file(path) == model.sha256
    )


def download_one(comfy_root: Path, staging: Path, model: ModelFile, token: str) -> None:
    from huggingface_hub import hf_hub_download

    destination = target_path(comfy_root, model)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if verified(destination, model):
        print(f"[verified] {model.destination}", flush=True)
        return

    if destination.exists():
        quarantine = destination.with_name(destination.name + ".invalid")
        destination.replace(quarantine)
        print(f"[warning] Moved invalid file to {quarantine}", flush=True)

    print(f"[download] {model.repo_id}/{model.filename}", flush=True)
    cached = Path(
        hf_hub_download(
            repo_id=model.repo_id,
            filename=model.filename,
            revision=model.revision,
            token=token,
            local_dir=staging / model.repo_id.replace("/", "--"),
        )
    )
    actual = sha256_file(cached)
    if actual != model.sha256:
        cached.unlink(missing_ok=True)
        raise RuntimeError(
            f"SHA-256 mismatch for {model.filename}: expected {model.sha256}, got {actual}"
        )

    temporary = destination.with_name(destination.name + ".partial")
    cached.replace(temporary)
    temporary.replace(destination)
    print(f"[installed] {model.destination}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comfy-root", type=Path, default=Path("/workspace/ComfyUI"))
    parser.add_argument("--status-file", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--print-manifest", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.print_manifest:
        print(json.dumps([asdict(model) for model in MODELS], indent=2))
        return 0

    write_status(args.status_file, "checking", completed=0, total=len(MODELS))
    try:
        missing = [
            model
            for model in MODELS
            if not verified(target_path(args.comfy_root, model), model)
        ]
        if args.check_only:
            for model in missing:
                print(f"[missing-or-invalid] {model.destination}")
            write_status(
                args.status_file,
                "missing" if missing else "ready",
                completed=len(MODELS) - len(missing),
                total=len(MODELS),
            )
            return 1 if missing else 0

        if not missing:
            write_status(args.status_file, "ready", completed=len(MODELS), total=len(MODELS))
            print("[ready] All MiniMax H3 model files passed SHA-256 verification.")
            return 0

        if os.getenv("MINIMAX_H3_AUTHORIZED") != "1":
            raise RuntimeError(
                "Set MINIMAX_H3_AUTHORIZED=1 to confirm you are authorized to download and use these weights."
            )
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
        if not token:
            raise RuntimeError(
                "Set HF_TOKEN to a Hugging Face token with access to all model repositories."
            )

        models_root = args.comfy_root / "models"
        models_root.mkdir(parents=True, exist_ok=True)
        required_bytes = sum(model.size_bytes for model in missing) + DISK_SAFETY_MARGIN_BYTES
        free_bytes = shutil.disk_usage(models_root).free
        if free_bytes < required_bytes:
            raise RuntimeError(
                "Not enough free model storage: "
                f"need at least {required_bytes / 1_000_000_000:.1f} GB, "
                f"but only {free_bytes / 1_000_000_000:.1f} GB is free."
            )

        staging = models_root / ".downloads"
        staging.mkdir(parents=True, exist_ok=True)
        write_status(
            args.status_file,
            "downloading",
            completed=0,
            total=len(missing),
            verified=len(MODELS) - len(missing),
        )
        for index, model in enumerate(missing, start=1):
            write_status(
                args.status_file,
                "downloading",
                completed=index - 1,
                total=len(missing),
                current=model.destination,
            )
            download_one(args.comfy_root, staging, model, token)
            write_status(
                args.status_file,
                "downloading",
                completed=index,
                total=len(missing),
                current=model.destination,
            )

        write_status(args.status_file, "ready", completed=len(MODELS), total=len(MODELS))
        shutil.rmtree(staging, ignore_errors=True)
        print("[ready] All MiniMax H3 model files passed SHA-256 verification.", flush=True)
        return 0
    except Exception as error:
        write_status(args.status_file, "failed", error=str(error))
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[fatal] {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
