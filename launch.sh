#!/bin/bash
<<<<<<< HEAD

cd /workspace/ComfyUI

exec python3 main.py --listen --port 8188
=======
echo "🔥 Running Maxed Out Installer..."
python3 /workspace/install_maxedout.py

echo "🚀 Starting ComfyUI..."
cd /workspace/ComfyUI
python3 main.py --listen 0.0.0.0 --port 8188 --enable-cors
>>>>>>> parent of 2884077 (Fixes)
