#!/bin/bash
set -e
export PYTHONPATH="/workspace/scripts:${PYTHONPATH}"

# Run the custom node installer
/opt/install_custom_nodes.sh

# 📦 Install core models once
# INSTALL_LOCK="/workspace/.flux_installed"

# if [ ! -f "$INSTALL_LOCK" ]; then
#     echo "⬇️  Downloading core FLUX models..."
#     python3 /workspace/scripts/download_core_models.py
#     touch "$INSTALL_LOCK"
# else
#     echo "✅ Core FLUX models already installed. Skipping download."
# fi

# 🔐 Start Patreon unlock server
echo "🔐 Starting Patreon unlock server..."
python3 -u /workspace/auth/app.py > /workspace/unlock.log 2>&1 &

# 🚀 Launch ComfyUI in the background
echo "🚀 Starting ComfyUI..."
python3 /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188 --enable-cors > /workspace/comfyui.log 2>&1 &
COMFYUI_PID=$!

echo "⏱️ Waiting for ComfyUI to become ready on port 8188..."

# Python-based port check (self-contained, no netcat needed)
until python3 -c "import socket; s = socket.socket(); s.settimeout(1); s.connect(('127.0.0.1', 8188)); s.close()" 2>/dev/null; do
  echo "ComfyUI not yet listening, waiting..."
  sleep 5
done

echo "✅ ComfyUI is now listening on port 8188."

# Keeps the container alive as long as ComfyUI runs
wait $COMFYUI_PID
