#!/bin/bash
set -e
export PYTHONPATH="/workspace/scripts:${PYTHONPATH}"

# Run the custom node installer
/opt/install_custom_nodes.sh

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

# 🚀 Launch ComfyUI in the background
echo "🚀 Starting ComfyUI..."
python3 /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188 > /workspace/comfyui.log 2>&1 &
COMFYUI_PID=$!

# Add JupyterLab startup here
echo "🚀 Starting JupyterLab..."
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root > /workspace/jupyterlab.log 2>&1 &
JUPYTER_PID=$! # Capture JupyterLab's PID if you want to explicitly wait for it later, or just include it in `wait`

# Python-based port check with timeout
CHECK_INTERVAL=5
TIMEOUT=60
ELAPSED=0

# ... (while loop code) ...
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

# Keeps the container alive as long as ComfyUI runs
wait $COMFYUI_PID $JUPYTER_PID
