#!/bin/bash
set -e
export PYTHONPATH="/workspace/scripts:${PYTHONPATH}"

echo "📦 Checking for core model files..."
if [ ! -f /workspace/ComfyUI/models/diffusion_models/flux1-dev-fp8.safetensors ]; then
    echo "⬇️  Downloading core FLUX models..."
    python3 /workspace/scripts/download_core_models.py
else
    echo "✅ Core FLUX models already present."
fi

echo "🔐 Starting Patreon unlock server..."
FLASK_RUN_PORT=7860 python3 /workspace/auth/app.py &

# Then start ComfyUI like normal
echo "🚀 Starting ComfyUI..."
exec python3 /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188 --enable-cors
