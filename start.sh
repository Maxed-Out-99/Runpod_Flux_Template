#!/bin/bash
set -e
export PYTHONPATH="/workspace/scripts:${PYTHONPATH}"

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
python3 /workspace/auth/app.py &

# 🚀 Launch ComfyUI
echo "🚀 Starting ComfyUI..."
exec python3 /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188 --enable-cors
