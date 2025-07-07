#!/bin/bash

echo "📦 Checking for core model files..."
cd /workspace

# Only run if models don't exist (fast boot if already present)
if [ ! -f /workspace/ComfyUI/models/diffusion_models/flux1-dev-fp8.safetensors ]; then
    echo "⬇️  Downloading core FLUX models..."
    cd /workspace/ComfyUI && python3 download_core_models.py
else
    echo "✅ Core FLUX models already present."
fi

echo "🚀 Starting ComfyUI..."
cd /workspace/ComfyUI
exec python3 main.py --listen 0.0.0.0 --port 8188 --enable-cors
