#!/bin/bash
set -e

CUSTOM_NODES_DIR="/workspace/ComfyUI/custom_nodes"
INSTALL_LOCK_FILE="${CUSTOM_NODES_DIR}/.pip_installed"

# Helper function to clone a repo if the directory doesn't already exist
# Usage: clone_repo "repo_url" "target_directory" ["--recursive"]
clone_repo() {
    local repo_url=$1
    local target_dir=$2
    local recursive_flag=$3
    
    if [ ! -d "$target_dir" ]; then
        echo "Cloning $repo_url..."
        git clone $recursive_flag "$repo_url" "$target_dir"
    else
        echo "Directory $target_dir already exists, skipping clone."
    fi
}

echo "▶️  Checking custom node installations..."

# Clone all node repositories
clone_repo "https://github.com/ltdrdata/ComfyUI-Manager.git" "${CUSTOM_NODES_DIR}/ComfyUI-Manager"
clone_repo "https://github.com/rgthree/rgthree-comfy.git" "${CUSTOM_NODES_DIR}/rgthree-comfy"
clone_repo "https://github.com/kijai/ComfyUI-KJNodes.git" "${CUSTOM_NODES_DIR}/ComfyUI-KJNodes"
clone_repo "https://github.com/Maxed-Out-99/ComfyUI-MaxedOut.git" "${CUSTOM_NODES_DIR}/ComfyUI-MaxedOut"
clone_repo "https://github.com/ltdrdata/ComfyUI-Impact-Pack.git" "${CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack"
clone_repo "https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git" "${CUSTOM_NODES_DIR}/ComfyUI-Impact-Subpack"
clone_repo "https://github.com/Fannovel16/comfyui_controlnet_aux.git" "${CUSTOM_NODES_DIR}/comfyui_controlnet_aux"
clone_repo "https://github.com/ssitu/ComfyUI_UltimateSDUpscale.git" "${CUSTOM_NODES_DIR}/ComfyUI_UltimateSDUpscale" "--recursive"
clone_repo "https://github.com/kijai/ComfyUI-Florence2.git" "${CUSTOM_NODES_DIR}/ComfyUI-Florence2"
clone_repo "https://codeberg.org/Gourieff/comfyui-reactor-node.git" "${CUSTOM_NODES_DIR}/comfyui-reactor-node"
clone_repo "https://github.com/chrisgoringe/cg-use-everywhere.git" "${CUSTOM_NODES_DIR}/cg-use-everywhere"
clone_repo "https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git" "${CUSTOM_NODES_DIR}/ComfyUI-Custom-Scripts"
clone_repo "https://github.com/city96/ComfyUI-GGUF.git" "${CUSTOM_NODES_DIR}/ComfyUI-GGUF"
clone_repo "https://github.com/kijai/ComfyUI-DepthAnythingV2.git" "${CUSTOM_NODES_DIR}/ComfyUI-DepthAnythingV2"
clone_repo "https://github.com/lldacing/ComfyUI_PuLID_Flux_ll.git" "${CUSTOM_NODES_DIR}/ComfyUI_PuLID_Flux_ll"
clone_repo "https://github.com/crystian/ComfyUI-Crystools.git" "${CUSTOM_NODES_DIR}/ComfyUI-Crystools"

# Install Python dependencies only if they haven't been installed before
if [ ! -f "$INSTALL_LOCK_FILE" ]; then
    echo "🐍 First time setup: Installing Python dependencies for custom nodes..."

    # Loop through directories and install requirements if they exist
    for dir in ${CUSTOM_NODES_DIR}/*/; do
        if [ -f "${dir}requirements.txt" ]; then
            echo "--- Installing requirements for ${dir} ---"
            pip install -r "${dir}requirements.txt"
        fi
    done

    # Run special installation scripts for specific nodes
    echo "--- Running installer for Impact Pack ---"
    python3 "${CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack/install.py"
    
    echo "--- Running installer for Reactor ---"
    python3 "${CUSTOM_NODES_DIR}/comfyui-reactor-node/install.py"
    
    echo "--- Upgrading gguf ---"
    pip install --upgrade gguf

    # Create the lock file to prevent this block from running again
    touch "$INSTALL_LOCK_FILE"
    echo "✅ Python dependencies installed."
else
    echo "✅ Python dependencies already installed, skipping."
fi

echo "✅ Custom node setup complete."