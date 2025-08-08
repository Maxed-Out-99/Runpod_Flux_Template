# ─── Imports ────────────────────────────────────────────────────────────────
import os
import sys
import subprocess
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask, redirect, request, send_file, send_from_directory
import jwt
from jwt import InvalidTokenError

sys.stdout.reconfigure(encoding="utf-8")

app = Flask(__name__)

# ─── Safe config (no secrets on pod) ────────────────────────────────────────
GATEWAY = os.environ.get("GATEWAY_URL", "https://auth.maxedout.ai")

with open("/workspace/public.pem", "rb") as f:
    PUBLIC_JWT_KEY = f.read()

# ─── Utilities ──────────────────────────────────────────────────────────────
def get_env_var(key, required=True, default=None):
    val = os.environ.get(key)
    if val is None:
        if required:
            raise RuntimeError(f"❌ Missing required environment variable: {key}")
        return default
    return val.strip()

def runpod_callback_url():
    """Build the stable public callback URL for this pod via RunPod proxy."""
    pod_id = get_env_var("RUNPOD_POD_ID")
    port = get_env_var("RUNPOD_PORT_7860_TCP_PORT", required=False, default="7860")
    return f"https://{pod_id}-{port}.proxy.runpod.net/callback"

def download_via_gateway(bearer_token: str, rel: str, dest_path: str):
    url = f"{GATEWAY}/deliver/{rel}"
    print(f"→ fetching {url} -> {dest_path}")
    r = requests.get(url, headers={"Authorization": f"Bearer {bearer_token}"}, stream=True, timeout=120)
    print(f"  status = {r.status_code}")
    if r.status_code != 200:
        try:
            print("  body:", r.text[:300])
        except Exception:
            pass
        raise RuntimeError(f"fetch failed: {url} -> {r.status_code}")

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    wrote = 0
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(1 << 20):
            if chunk:
                f.write(chunk)
                wrote += len(chunk)
    print(f"  wrote {wrote} bytes to {dest_path}")

# ─── Static pages & 404 ────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return redirect("/")

@app.route("/success")
def success():
    print("✅ Success page reached.")
    return send_file("/workspace/auth/success.html")

@app.route("/")
def index():
    print("✅ Index page served.")
    return send_file("/workspace/auth/index.html")

# ─── Auth flow (delegated to gateway) ──────────────────────────────────────
@app.route("/auth")
def auth():
    """
    Start OAuth by handing off to the gateway.
    The gateway owns Patreon OAuth + entitlement checks.
    """
    cb = runpod_callback_url()
    return redirect(f"{GATEWAY}/start?pod_callback={cb}")

@app.route("/callback")
@app.route("/callback/")
def callback():
    """
    Gateway redirects here with ?token=<JWT>.
    We verify the JWT with our public key (RS256), then pull gated files
    through the gateway using that same JWT (one-time use).
    """
    # Reuse success within 24h if present
    token_file = "/workspace/.flux_token"
    if os.path.exists(token_file):
        try:
            ts = datetime.fromisoformat(open(token_file).read().strip())
            if datetime.now(timezone.utc) - ts <= timedelta(hours=24):
                print("✅ Already unlocked within last 24h")
                return redirect("/success")
        except Exception as e:
            print(f"⚠️ Couldn't parse timestamp: {e}")
            try:
                os.remove(token_file)
            except Exception:
                pass

    token = request.args.get("token")
    if not token:
        return "Missing token", 400

    if not PUBLIC_JWT_KEY:
        return "Server misconfigured: missing PUBLIC_JWT_KEY_PEM", 500

    # Verify JWT issued by gateway
    try:
        claims = jwt.decode(token, PUBLIC_JWT_KEY, algorithms=["RS256"], audience="runpod")
        # Optional: sanity logs
        print(f"🔐 JWT OK for sub={claims.get('sub')} pod={claims.get('pod_id')} exp={claims.get('exp')}")
    except InvalidTokenError as e:
        print("JWT error:", e)
        return "Invalid token", 403

    # Pull gated assets (workflow + helper scripts) via the gateway
    try:
        # Main workflow
        download_via_gateway(
            token,
            "workflow",
            "/workspace/ComfyUI/user/default/workflows/Mega Flux v1.json",
        )

        # Helper scripts
        scripts = [
            "download_all_mega_files.py",
            "download_small_mega_files.py",
            "download_all_mega_files_fp8.py",
        ]
        for name in scripts:
            download_via_gateway(
                token,
                f"script?name={name}",
                f"/workspace/scripts/{name}",
            )

        with open(token_file, "w") as f:
            f.write(datetime.now(timezone.utc).isoformat())

        return redirect("/success")
    except Exception as e:
        print(f"❌ Download via gateway failed: {e}")
        return "Failed to fetch gated files", 500

# ─── Download status & triggers (unchanged behavior) ───────────────────────
@app.route("/download/status/<version>")
def download_status(version):
    log_file_path = "/workspace/logs/power_user_downloads.log"
    done_file = f"/workspace/logs/download_{version}.done"

    if os.path.exists(done_file):
        return {"status": "complete"}

    if not os.path.exists(log_file_path):
        return {"status": "starting"}

    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        overall_line = next((line for line in reversed(lines) if line.startswith("OVERALL::")), "Waiting for overall progress...")
        detail_line = next((line for line in reversed(lines) if line.startswith("   DETAIL::")), "")
        info_line = next((line for line in reversed(lines) if line.startswith("INFO::")), "")

        return {
            "status": "downloading",
            "overall": overall_line.strip(),
            "detail": detail_line.strip(),
            "info": info_line.strip(),
        }
    except Exception as e:
        print(f"Error reading log status: {e}")
        return {"status": "error"}

@app.route("/download/<version>")
def download_mega(version):
    script_map = {
        "all": "download_all_mega_files.py",
        "small": "download_small_mega_files.py",
        "all_fp8": "download_all_mega_files_fp8.py",
    }
    if version not in script_map:
        return "Invalid version specified", 404

    script_name = script_map[version]
    script_path = os.path.join("/workspace/scripts", script_name)

    if not os.path.exists(script_path):
        return f"Script {script_name} not found.", 500

    log_file_path = "/workspace/logs/power_user_downloads.log"
    done_file = f"/workspace/logs/download_{version}.done"
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    # Clean old files
    if os.path.exists(done_file):
        os.remove(done_file)
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    try:
        with open(log_file_path, "a") as log_file:
            print(f"🚀 Starting download for '{version}'. Log: {log_file_path}")
            subprocess.Popen(
                ["python3", "-u", script_path],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd="/workspace/scripts",
            )
    except Exception as e:
        print(f"🔥 CRITICAL ERROR starting subprocess for {script_name}: {e}")
        return "An unexpected error occurred while trying to start the download.", 500

    return redirect(f"/downloading/{version}")

@app.route("/downloading/<version>")
def downloading_page(version):
    if version not in ["all", "small", "all_fp8"]:
        return "Invalid version specified", 404
    return send_file("/workspace/auth/downloading.html")

# Serve images
@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory("/workspace/auth/images", filename)

# ─── Main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
