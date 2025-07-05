#!/bin/bash

echo "🔥 Running Maxed Out Installer..."
cd /workspace/ComfyUI
python3 /workspace/install_maxedout.py

echo "🚀 Starting ComfyUI..."
exec python3 main.py --listen 0.0.0.0 --port 8188 --enable-cors
