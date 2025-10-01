#!/bin/bash
set -e

# --- Minimal PV-safe bootstrap (no behavior change to your flow) ---
# Make sure the persistent volume mount exists
mkdir -p /workspace

# Seed ComfyUI onto the PV on first run (includes .git, configs, etc.)
if [[ ! -d /workspace/ComfyUI ]]; then
  echo "[init] Seeding ComfyUI into /workspace..."
  cp -a /opt/ComfyUI /workspace/ComfyUI
fi

# Seed your scripts and auth app to the PV (first run only)
if [[ ! -d /workspace/scripts ]]; then
  cp -a /opt/scripts /workspace/scripts
fi

if [[ ! -d /workspace/auth ]]; then
  cp -a /opt/auth /workspace/auth
fi

# Ensure runtime dirs exist (ComfyUI will use these)
mkdir -p /workspace/{input,output,temp,user/default/workflows}

# Convenience: keep /ComfyUI path available for anything that expects it
rm -rf /ComfyUI 2>/dev/null || true
ln -s /workspace/ComfyUI /ComfyUI
# --- end minimal bootstrap ---

# 📦 Install custom nodes once
NODES_LOCK="/workspace/.custom_nodes_installed"
if [ ! -f "$NODES_LOCK" ]; then
    echo "⬇️ Installing custom nodes..."
    bash /opt/install_custom_nodes.sh
    touch "$NODES_LOCK"
else
    echo "✅ Custom nodes already installed. Skipping."
fi

export PYTHONPATH="/workspace/scripts:${PYTHONPATH}"

echo "🔥 STARTING FLUX V1 @ $(date) — Commit: $(git rev-parse HEAD 2>/dev/null || echo unknown)"

# 📦 Install core models once
INSTALL_LOCK="/workspace/.flux_installed"

if [ ! -f "$INSTALL_LOCK" ]; then
    echo "⬇️  Downloading core FLUX models..."
    python3 /workspace/scripts/download_core_models.py
    touch "$INSTALL_LOCK"
else
    echo "✅ Core FLUX models already installed. Skipping download."
fi

# 🔐 Start Patreon unlock server
echo "🔐 Starting Patreon unlock server..."
python3 -u /workspace/auth/app.py > /workspace/unlock.log 2>&1 &
sleep 2

# 🚀 Launch ComfyUI in the background
echo "🚀 Starting ComfyUI..."
python3 /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188 > /workspace/comfyui.log 2>&1 &
COMFYUI_PID=$!
sleep 2

# ─── CORRECTED JUPYTER STARTUP ───────────────────────────────────────────
echo "🚀 Starting JupyterLab..."

# Respect RunPod's proxy path when it is provided so the UI doesn't 404 when
# opened through the control panel button. Default to the root when the
# environment variable is not set.
JUPYTER_BASE_URL="${RUNPOD_JUPYTER_PROXY_PATH:-/}"
if [[ -n "$JUPYTER_BASE_URL" && "${JUPYTER_BASE_URL:0:1}" != "/" ]]; then
  JUPYTER_BASE_URL="/${JUPYTER_BASE_URL}"
fi

# Provide sane defaults for other frequently customised settings while still
# allowing overrides through environment variables.
JUPYTER_DEFAULT_URL="${RUNPOD_JUPYTER_DEFAULT_URL:-/lab}"
if [[ -n "$JUPYTER_DEFAULT_URL" && "${JUPYTER_DEFAULT_URL:0:1}" != "/" ]]; then
  JUPYTER_DEFAULT_URL="/${JUPYTER_DEFAULT_URL}"
fi

JUPYTER_ROOT_DIR="${RUNPOD_JUPYTER_ROOT:-/workspace}"

echo "   ↳ Base URL: ${JUPYTER_BASE_URL}"
echo "   ↳ Default URL: ${JUPYTER_DEFAULT_URL}"
echo "   ↳ Root dir: ${JUPYTER_ROOT_DIR}"

# Start Jupyter in the background with explicit base URL configuration.
jupyter lab \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --allow-root \
  --ServerApp.base_url="${JUPYTER_BASE_URL}" \
  --ServerApp.default_url="${JUPYTER_DEFAULT_URL}" \
  --ServerApp.root_dir="${JUPYTER_ROOT_DIR}" \
  --ServerApp.allow_remote_access=True \
  --ServerApp.trust_xheaders=True \
  > /workspace/jupyterlab.log 2>&1 &
JUPYTER_PID=$!

# Wait for the Jupyter server to be fully running
echo "✅ Waiting for JupyterLab server to respond..."
while ! jupyter server list > /dev/null 2>&1; do
  sleep 1
done

# Get the token directly from the server command (robust against either single
# objects or JSON lists depending on the Jupyter version)
TOKEN=$(jupyter server list --json | jq -r '.[0].token // .token')
SERVER_URL=$(jupyter server list --json | jq -r '.[0].url // .url')

# Print the clean token for easy copying
echo ""
echo "JUPYTERLAB TOKEN: ${TOKEN}"
echo "JUPYTERLAB URL: ${SERVER_URL}${JUPYTER_DEFAULT_URL#/}" 
echo "(You may need this to log in to JupyterLab)"
echo ""
# ───────────────────────────────────────────────────────────────────────────

# Wait for ComfyUI to be ready
CHECK_INTERVAL=5
TIMEOUT=60
ELAPSED=0

while ! python3 -c "import socket; s = socket.socket(); s.settimeout(1); s.connect(('127.0.0.1', 8188)); s.close()" 2>/dev/null; do
  if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    cat /workspace/comfyui.log
    exit 1
  fi
  sleep "$CHECK_INTERVAL"
  ELAPSED=$((ELAPSED + CHECK_INTERVAL))
done

# Add these lines to confirm ComfyUI is ready
echo "✅ ComfyUI is listening on port 8188. Startup complete."
echo ""
echo ""

# Keeps the container alive as long as ComfyUI and JupyterLab run
wait $COMFYUI_PID $JUPYTER_PID
