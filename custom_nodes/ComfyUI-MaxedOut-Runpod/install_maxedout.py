#!/usr/bin/env python

from __future__ import annotations
import sys, subprocess, time, atexit, signal, requests, hashlib, os
from pathlib import Path

# --- Configuration for RunPod ---
# Set to True to also download the faster, lower-quality Schnell model.
DOWNLOAD_SCHNELL = True
# Set a specific commit hash for reproducibility.
HF_COMMIT = "7e036e0bdf2cfd04d07668b768bc887b583f745c"

# --- Global Variables ---
BASE_URL = (
    "https://huggingface.co/MaxedOut/ComfyUI-Starter-Packs"
    f"/resolve/{HF_COMMIT}"
)
MODEL_DIR = Path("/workspace/ComfyUI/models")
LOG_DIR = Path("install_logs_mxd")
TEST_MODE = "--test" in sys.argv

# --- Stream redirection for logging ---
_orig_stdout = sys.stdout
_orig_stderr = sys.stderr
user_cancelled: bool = False

# --- Constants ---
CHUNK = 8192
TIMEOUT = 60
RETRIES = 3
PROG_INT = 0.1
LOG_DELAY = 0  # Set to 0 for fast, non-interactive logging.
FAILED_FILES = []

# ── Graceful Exit Handler ───────────────────────────────────────────────────
def handle_interrupt(sig, frame):
    """SIGINT handler – mark cancel, flush logs, exit fast."""
    global user_cancelled
    user_cancelled = True
    _orig_stdout.write("\n🟥 Installer cancelled by user. Partial downloads may remain.\n")
    try:
        _orig_stdout.flush()
        _orig_stderr.flush()
        if 'log_fp' in globals() and not log_fp.closed:
            log_fp.flush()
    except Exception:
        pass
    sys.exit(130)

signal.signal(signal.SIGINT, handle_interrupt)

# ── Logging Setup ───────────────────────────────────────────────────────────
def log(msg: str, **kwargs) -> None:
    """Prints a message to the console and log file."""
    print(msg)
    # The time.sleep delay is removed for faster server execution.

# ── Core Utility Functions ──────────────────────────────────────────────────
def _get_local_sha256(file_path: Path) -> str | None:
    """Calculates the SHA256 hash of a local file."""
    if not file_path.exists():
        return None
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(CHUNK):
                sha256.update(chunk)
        return sha256.hexdigest()
    except IOError as e:
        log(f"⚠️  Could not read file for hashing: {file_path.name} - {e}")
        return None

def _remote_size(url: str) -> int | None:
    """Gets the size of a remote file."""
    for attempt in range(RETRIES):
        try:
            h = requests.head(url, allow_redirects=True, timeout=TIMEOUT)
            cl = h.headers.get("Content-Length")
            if cl and cl.isdigit():
                return int(cl)
        except Exception:
            log(f"⚠️  HEAD request failed (attempt {attempt+1}/{RETRIES}) for size check.")
            time.sleep(2 * 2**attempt)
    log("🚫 Failed to get remote file size after multiple attempts.")
    return None

# ── Dependency Installation ────────────────────────────────────────────────
def install_pip_package(package_name: str, install_args: list[str] = None):
    """Installs a Python package using pip if it's not already installed."""
    try:
        __import__(package_name)
        log(f"✅ {package_name} is already installed.")
        return
    except ImportError:
        log(f"📦 {package_name} not found. Installing...")

    args = install_args if install_args else [package_name]
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", *args],
            capture_output=True, text=True, check=True,
        )
        log(f"   ✅ {package_name} installed successfully.")
    except subprocess.CalledProcessError as e:
        log(f"   ❌ Failed to install {package_name}.")
        log(f"   PIP Error: {e.stderr.strip()}")
        FAILED_FILES.append((package_name, "pip install failed"))
    except Exception as e:
        log(f"   ❌ An unexpected error occurred during {package_name} installation: {e}")
        FAILED_FILES.append((package_name, "unexpected installation exception"))

def clone_custom_nodes():
    """Clones or updates the custom nodes repository."""
    repo_url = "https://github.com/Maxed-Out-99/ComfyUI-MaxedOut.git"
    target_dir = Path("custom_nodes/ComfyUI-MaxedOut")

    if target_dir.exists() and (target_dir / ".git").exists():
        log("\n🔁 Updating existing MaxedOut custom nodes...")
        try:
            subprocess.run(
                ["git", "-C", str(target_dir), "pull"],
                capture_output=True, text=True, check=True
            )
            log("   ✅ MaxedOut custom nodes are up to date.")
        except subprocess.CalledProcessError as e:
            log(f"   ❌ Git pull failed: {e.stderr}")
            FAILED_FILES.append(("custom_nodes/ComfyUI-MaxedOut", "Git pull failed"))
        return

    if target_dir.exists():
        log("✅ MaxedOut custom nodes folder found (non-git). Skipping clone.")
        return

    log("📦 Cloning MaxedOut custom nodes...")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
            check=True, capture_output=True, text=True
        )
        log("   ✅ Cloned MaxedOut custom nodes successfully.")
    except subprocess.CalledProcessError as e:
        log(f"   ❌ Failed to clone MaxedOut custom nodes: {e.stderr}")
        FAILED_FILES.append(("custom_nodes/ComfyUI-MaxedOut", "Initial Git clone failed"))

# ── File Downloading Logic ──────────────────────────────────────────────────
def _download_once(url: str, tmp_path: Path, resume: bool = False) -> int:
    """Performs a single download attempt, with resume logic."""
    range_header, mode, start_byte = {}, "wb", 0
    if resume and tmp_path.exists():
        start_byte = tmp_path.stat().st_size
        if start_byte > 0:
            range_header = {"Range": f"bytes={start_byte}-"}
            mode = "ab"

    with requests.get(url, stream=True, timeout=(10, 300), headers=range_header) as r:
        r.raise_for_status()
        total_expected = int(r.headers.get("Content-Length", 0)) + start_byte
        written, last_print = start_byte, 0

        with open(tmp_path, mode) as f:
            for chunk in r.iter_content(chunk_size=CHUNK):
                f.write(chunk)
                written += len(chunk)
                if TEST_MODE and written >= 1024 * 1024: # 1MB limit for test mode
                    log(f"🧪 Test mode: stopped at 1 MB for {tmp_path.name}")
                    break
                now = time.time()
                if now - last_print >= PROG_INT or written == total_expected:
                    pct = f" ({written / total_expected:.1%})" if total_expected > 0 else ""
                    _orig_stdout.write(f"\r   📥 {tmp_path.name}{pct}  ")
                    _orig_stdout.flush()
                    last_print = now
    
    _orig_stdout.write("\n")
    _orig_stdout.flush()

    if total_expected and written != total_expected and not TEST_MODE:
        raise IOError(f"Corrupted download: size mismatch (got {written}, expected {total_expected})")
    
    return written

def download(remote_path: str, local_path: Path, expected_sha256: str) -> None:
    """Main download wrapper with retries, resume, and hash checking."""
    if local_path.exists():
        log(f"✅ File already exists: {local_path.name}. Verifying hash...")
        local_hash = _get_local_sha256(local_path)
        if local_hash and local_hash.lower() == expected_sha256.lower():
            log("   ✅ Hash matches. Skipping download.")
            return
        else:
            log("   ⚠️ Hash mismatch or unreadable. Re-downloading.")
            local_path.unlink()

    url = f"{BASE_URL}/{remote_path}"
    tmp_path = local_path.with_suffix(".part")
    local_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, RETRIES + 1):
        try:
            log(f"⬇️  Downloading {local_path.name} (Attempt {attempt}/{RETRIES})")
            resume_flag = tmp_path.exists()
            _download_once(url, tmp_path, resume=resume_flag)
            
            final_hash = _get_local_sha256(tmp_path)
            if final_hash and final_hash.lower() == expected_sha256.lower():
                tmp_path.rename(local_path)
                log(f"   ✅ Download complete and verified: {local_path.name}")
                return
            else:
                raise IOError(f"Corrupted download - SHA256 mismatch.")
        
        except Exception as e:
            log(f"   ⚠️ Download failed: {e}")
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError as unlink_err:
                    log(f"   ⚠️ Could not delete .part file: {unlink_err}")
            if attempt < RETRIES:
                time.sleep(2 * 2**attempt)
            else:
                log(f"   ❌ Giving up after {RETRIES} attempts.")
                FAILED_FILES.append((remote_path, str(local_path)))

# ── Model File Lists ────────────────────────────────────────────────────────
def get_model_files(schnell: bool = False):
    """
    Returns a hardcoded list of the highest-quality models for RunPod.
    Tier A: fp8 UNETs and fp16 T5 for high VRAM/RAM systems.
    """
    files = [
        # T5 and CLIP Models
        ("Flux1/clip/t5xxl_fp16.safetensors", "clip/t5xxl_fp16.safetensors", "6e480b09fae049a72d2a8c5fbccb8d3e92febeb233bbe9dfe7256958a9167635"),
        ("Flux1/clip/clip_l.safetensors", "clip/clip_l.safetensors", "660c6f5b1abae9dc498ac2d21e1347d2abdb0cf6c0c0c8576cd796491d9a6cdd"),
        
        # FP8 UNETs
        ("Flux1/unet/Dev/flux1-dev-fp8.safetensors", "diffusion_models/flux1-dev-fp8.safetensors", "1be961341be8f5307ef26c787199f80bf4e0de3c1c0b4617095aa6ee5550dfce"),
        ("Flux1/unet/Fill/flux1-fill-dev-fp8.safetensors", "diffusion_models/flux1-fill-dev-fp8.safetensors", "0320d505ca42bca99c5bd600b1839ced2b2e980ea985917965d411d98a710729"),
        ("Flux1/unet/Canny/flux1-canny-dev-fp8.safetensors", "diffusion_models/flux1-canny-dev-fp8.safetensors", "3225da20cfcf18a0537147acb5f57fa11f75ff568827cadcfcbba3289f136574"),
        ("Flux1/unet/Depth/flux1-depth-dev-fp8.safetensors", "diffusion_models/flux1-depth-dev-fp8.safetensors", "4206c6b3f737d350170e2ac9f5b4facf15cb25f1da813608023caf6a34d4edef"),
        
        # FP16 UNETs
        ("Flux1/unet/Fill/flux1-fill-dev-fp16.safetensors", "diffusion_models/flux1-fill-dev-fp16.safetensors", "03e289f530df51d014f48e675a9ffa2141bc003259bf5f25d75b957e920a41ca"),
        ("Flux1/unet/Canny/flux1-canny-dev-fp16.safetensors", "diffusion_models/flux1-canny-dev-fp16.safetensors", "996876670169591cb412b937fbd46ea14cbed6933aef17c48a2dcd9685c98cdb"),
        ("Flux1/unet/Depth/flux1-depth-dev-fp16.safetensors", "diffusion_models/flux1-depth-dev-fp16.safetensors", "41360d1662f44ca45bc1b665fe6387e91802f53911001630d970a4f8be8dac21"),
        ("Flux1/unet/Schnell/flux1-schnell-fp16.safetensors", "diffusion_models/flux1-schnell-fp16.safetensors", "9403429e0052277ac2a87ad800adece5481eecefd9ed334e1f348723621d2a0a"),
        ("Flux1/unet/Dev/flux1-dev-fp16.safetensors", "diffusion_models/flux1-dev-fp16.safetensors", "4610115bb0c89560703c892c59ac2742fa821e60ef5871b33493ba544683abd7"),
    ]
    if schnell:
        files.append(("Flux1/unet/Schnell/flux1-schnell-fp8.safetensors", "diffusion_models/flux1-schnell-fp8.safetensors", "bbdfba27fed8ff3be237523fb37b83821a6c4bbaa1db43ef9288767d0e4042fb"))

    # List of essential supporting models
    always_download = [
        ("Flux1/vae/ae.safetensors", "vae/ae.safetensors", "afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38"),
        ("Flux1/PuLID/pulid_flux_v0.9.1.safetensors", "pulid/pulid_flux_v0.9.1.safetensors", "92c41c3af322b02e58e1b32842e4601e08c8f16ec1fe80089dbe957df510f51d"),
        ("Flux1/Style_Models/flux1-redux-dev.safetensors", "style_models/flux1-redux-dev.safetensors", "a1b3bdcb4bdc58ce04874b9ca776d61fc3e914bb6beab41efb63e4e2694dca45"),
        ("Flux1/clip_vision/sigclip_vision_patch14_384.safetensors", "clip_vision/sigclip_vision_patch14_384.safetensors", "1fee501deabac72f0ed17610307d7131e3e9d1e838d0363aa3c2b97a6e03fb33"),
        ("Upscale_Models/RealESRGAN_x2plus.pth", "upscale_models/RealESRGAN_x2plus.pth", "49fafd45f8fd7aa8d31ab2a22d14d91b536c34494a5cfe31eb5d89c2fa266abb"),
        ("Upscale_Models/4x-UltraSharp.pth", "upscale_models/4x-UltraSharp.pth", "a5812231fc936b42af08a5edba784195495d303d5b3248c24489ef0c4021fe01"),
        ("Adetailer/sams/sam_vit_b_01ec64.pth", "sams/sam_vit_b_01ec64.pth", "ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912"),
        ("Adetailer/Ultralytics/bbox/face_yolov8m.pt", "ultralytics/bbox/face_yolov8m.pt", "e3893a92c5c1907136b6cc75404094db767c1e0cfefe1b43e87dad72af2e4c9f"),
        ("Adetailer/Ultralytics/bbox/hand_yolov8s.pt", "ultralytics/bbox/hand_yolov8s.pt", "30878cea9870964d4a238339e9dcff002078bbbaa1a058b07e11c167f67eca1c"),
        ("Flux1/Controlnets/flux_shakker_labs_union_pro-fp8.safetensors", "controlnet/flux_shakker_labs_union_pro-fp8.safetensors", "9535c82da8b4abb26eaf827e60cc3da401ed676ea85787f17b168a671b27e491"),
        ("FaceRestore_Models/codeformer.pth", "facerestore_models/codeformer.pth", "1009e537e0c2a07d4cabce6355f53cb66767cd4b4297ec7a4a64ca4b8a5684b7"),
        ("FaceRestore_Models/GFPGANv1.4.pth", "facerestore_models/GFPGANv1.4.pth", "e2cd4703ab14f4d01fd1383a8a8b266f9a5833dacee8e6a79d3bf21a1b6be5ad"),
        ("Flux1/LoRas/navi_flux_v1.safetensors", "loras/navi_flux_v1.safetensors", "8c60d9038512bba3964bba0768771c2724a76cd41e5cfb5543dca8b84570e303"),
    ]
    return files + always_download

# ── Main Execution ──────────────────────────────────────────────────────────
def main():
    """Main execution block."""
    global log_fp # Make log_fp accessible to shutdown handler
    
    # --- Check for prerequisites ---
    if not (Path.cwd() / "models").exists():
        _orig_stdout.write("\n[ERROR] 'models' folder not found. This script must be run from your ComfyUI directory.\n")
        sys.exit(1)
    if subprocess.call(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
        _orig_stdout.write("\n[ERROR] Git is not installed or not in PATH. Please install Git.\n")
        sys.exit(1)

    # --- Setup Logging ---
    LOG_DIR.mkdir(exist_ok=True)
    log_file_path = LOG_DIR / f"runpod_flux_install_{time.strftime('%Y%m%d-%H%M%S')}.txt"
    log_fp = open(log_file_path, "a", encoding="utf8", buffering=1)

    class _Tee:
        def __init__(self, stream, fp): self._stream, self._fp = stream, fp
        def write(self, data): self._stream.write(data); self._fp.write(data)
        def flush(self): self._stream.flush(); self._fp.flush()
        def __getattr__(self, name): return getattr(self._stream, name)

    sys.stdout = _Tee(sys.stdout, log_fp)
    sys.stderr = _Tee(sys.stderr, log_fp)
    atexit.register(_shutdown_logging)

    log(f"=== FLUX Automated Installer Log ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")
    if TEST_MODE:
        log("🧪 TEST MODE ENABLED: Downloads will stop after 1 MB.")
    
    # --- Install Dependencies ---
    log("\n--- Installing Dependencies ---")
    install_pip_package("facexlib", ["--use-pep517", "facexlib"])
    install_pip_package("insightface")
    clone_custom_nodes()

    # --- Download Models ---
    log("\n--- Downloading Models ---")
    try:
        requests.head("https://huggingface.co", timeout=10)
    except Exception:
        log("❌ No outbound connection to Hugging Face. Check your internet/firewall.")
        sys.exit(1)
    
    queue = get_model_files(schnell=DOWNLOAD_SCHNELL)
    total = len(queue)
    log(f"🟢 Download queue contains {total} files. Starting...")

    for i, (repo, local, sha256) in enumerate(queue, 1):
        log(f"\n--- File {i}/{total} ---")
        download(repo, MODEL_DIR / local, sha256)

    # --- Final Summary ---
    log("\n\n=================> MEGA FLUX INSTALLER COMPLETE <=================\n")
    if FAILED_FILES:
        log("❌ Some steps failed:\n")
        for item, reason in FAILED_FILES:
            log(f" - Item: {item}, Reason: {reason}")
    else:
        log("✅ All files and dependencies installed successfully.")
    
    log(f"\nLogs saved to {log_file_path} for future reference.\n")

def _shutdown_logging():
    """Restores stdout/stderr and closes the log file."""
    if 'log_fp' in globals() and not log_fp.closed:
        log_fp.close()
    sys.stdout = _orig_stdout
    sys.stderr = _orig_stderr
    
    # Final message to the original console
    if user_cancelled:
        _orig_stdout.write("⚠️ Installer was cancelled.\n")
    elif FAILED_FILES:
        _orig_stdout.write("⚠️ Installer completed with errors. Check the log for details.\n")
    else:
        _orig_stdout.write("✅ Installer finished successfully.\n")
    _orig_stdout.flush()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        user_cancelled = True
        log("\n[EXIT] Install cancelled by user.\n")
    except Exception as e:
        log(f"\n❌ UNEXPECTED ERROR:\n{type(e).__name__}: {e}")
        import traceback
        log(traceback.format_exc())
    finally:
        # The atexit handler will perform the final cleanup.
        pass
