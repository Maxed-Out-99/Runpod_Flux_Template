#!/bin/bash
set -e
export PYTHONPATH="/workspace/scripts:${PYTHONPATH}"

# 🌐 Dynamically determine the correct redirect URI
HOSTNAME=$(curl -s http://169.254.169.254/latest/meta-data/public-hostname || hostname)
export PATREON_REDIRECT_URI="https://${HOSTNAME}:7860/callback"
echo "🔁 Using PATREON_REDIRECT_URI=$PATREON_REDIRECT_URI"

echo "📦 Checking for core model files..."
if [ ! -f /workspace/ComfyUI/models/diffusion_models/flux1-dev-fp8.safetensors ]; then
    echo "⬇️  Downloading core FLUX models..."
    python3 /workspace/scripts/download_core_models.py
else
    echo "✅ Core FLUX models already present."
fi

echo "🔐 Starting Patreon unlock server..."
python3 /workspace/auth/app.py > /workspace/unlock.log 2>&1 &

echo "🚀 Starting ComfyUI..."
exec python3 /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188 --enable-cors
