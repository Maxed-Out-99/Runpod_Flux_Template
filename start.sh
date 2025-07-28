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
CHECK_INTERVAL=2
TIMEOUT=90
ELAPSED=0

# Function to check a port
wait_for_port() {
  local port=$1
  local service_name=$2
  local elapsed=0
  echo "⌛ Waiting for $service_name on port $port..."
  while ! nc -z 127.0.0.1 $port >/dev/null 2>&1; do
    if [ "$elapsed" -ge "$TIMEOUT" ]; then
      echo "❌ ERROR: $service_name failed to start within $TIMEOUT seconds."
      # Optional: show the log for the failed service
      [ -f "/workspace/${service_name,,}.log" ] && cat "/workspace/${service_name,,}.log"
      exit 1
    fi
    sleep "$CHECK_INTERVAL"
    elapsed=$((elapsed + CHECK_INTERVAL))
  done
  echo "✅ $service_name is ready."
}

# Wait for all services
wait_for_port 8188 "ComfyUI"
wait_for_port 8888 "JupyterLab"
wait_for_port 7860 "Patreon Unlock Server"

echo ""
echo "✅ All services are running. Startup complete."
echo ""

# Keeps the container alive by waiting for the primary processes
wait $COMFYUI_PID $JUPYTER_PID
