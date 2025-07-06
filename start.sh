#!/bin/bash

echo "🚀 Starting ComfyUI..."
cd /workspace/ComfyUI
touch /workspace/healthcheck
exec python3 main.py --listen 0.0.0.0 --port 8188 --enable-cors
