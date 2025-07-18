#!/bin/bash
set -e

CUSTOM_NODES_DIR="/workspace/ComfyUI/custom_nodes"
INSTALL_LOCK_FILE="${CUSTOM_NODES_DIR}/.pip_installed"

# Updated helper function now accepts an optional commit hash
# Usage: clone_repo "repo_url" "target_directory" "recursive_flag" "commit_hash"
clone_repo() {
    local repo_url=$1
    local target_dir=$2
    local recursive_flag=$3
    local commit_hash=$4
    
    if [ ! -d "$target_dir" ]; then
        echo "Cloning $repo_url..."
        git clone $recursive_flag "$repo_url" "$target_dir" || true
        
        if [ -n "$commit_hash" ]; then
            echo "--- Checking out specific commit: $commit_hash ---"
            (cd "$target_dir" && git checkout "$commit_hash")
        fi
    else
        echo "Directory $target_dir already exists, skipping clone."
    fi
}

echo "▶️  Checking custom node installations..."

# Clone all node repositories with specific, known-good commit hashes
clone_repo "https://github.com/ltdrdata/ComfyUI-Manager.git" "${CUSTOM_NODES_DIR}/ComfyUI-Manager" "" "e894bd9f2420df674ace899a0be3f2e1b21fa177"
clone_repo "https://github.com/rgthree/rgthree-comfy.git" "${CUSTOM_NODES_DIR}/rgthree-comfy" "" "944d5353a1b0a668f40844018c3dc956b95a67d7"
clone_repo "https://github.com/kijai/ComfyUI-KJNodes.git" "${CUSTOM_NODES_DIR}/ComfyUI-KJNodes" "" "ad37ce656c13e9abea002b46e3a89be3dba32355"
clone_repo "https://github.com/Maxed-Out-99/ComfyUI-MaxedOut.git" "${CUSTOM_NODES_DIR}/ComfyUI-MaxedOut" "" "5920ada2cd84e10ccf624cfae49c70db0fe47621"
# clone_repo "https://github.com/ltdrdata/ComfyUI-Impact-Pack.git" "${CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack" "" "b3a815b43d987022542715b351ce3c2c02c902db"
# clone_repo "https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git" "${CUSTOM_NODES_DIR}/ComfyUI-Impact-Subpack" "" "5b4e55058ae48e18e1c6d974000461ad1e240135"
clone_repo "https://github.com/Fannovel16/comfyui_controlnet_aux.git" "${CUSTOM_NODES_DIR}/comfyui_controlnet_aux" "" "59b027e088c1c8facf7258f6e392d16d204b4d27"
clone_repo "https://github.com/ssitu/ComfyUI_UltimateSDUpscale.git" "${CUSTOM_NODES_DIR}/ComfyUI_UltimateSDUpscale" "--recursive" "95fb26043d341c79246f0e137aabc64c19d67d37"
clone_repo "https://github.com/kijai/ComfyUI-Florence2.git" "${CUSTOM_NODES_DIR}/ComfyUI-Florence2" "" "de485b65b3e1b9b887ab494afa236dff4bef9a7e"
clone_repo "https://github.com/Gourieff/ComfyUI-ReActor.git" "${CUSTOM_NODES_DIR}/comfyui-reactor-node" "" "9b17e4cea53769d7157e507659adbbe09a3114fe"
clone_repo "https://github.com/chrisgoringe/cg-use-everywhere.git" "${CUSTOM_NODES_DIR}/cg-use-everywhere" "" "a834f09f3889264f192711971ca624128650a250"
clone_repo "https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git" "${CUSTOM_NODES_DIR}/ComfyUI-Custom-Scripts" "" "aac13aa7ce35b07d43633c3bbe654a38c00d74f5"
clone_repo "https://github.com/city96/ComfyUI-GGUF.git" "${CUSTOM_NODES_DIR}/ComfyUI-GGUF" "" "b3ec875a68d94b758914fd48d30571d953bb7a54"
clone_repo "https://github.com/kijai/ComfyUI-DepthAnythingV2.git" "${CUSTOM_NODES_DIR}/ComfyUI-DepthAnythingV2" "" "d505cbca99803fc63327b8305618a23e59a18b42"
clone_repo "https://github.com/lldacing/ComfyUI_PuLID_Flux_ll.git" "${CUSTOM_NODES_DIR}/ComfyUI_PuLID_Flux_ll" "" "ba90657fe6ffa8072ac169a949bfa5e4153bf48a"
clone_repo "https://github.com/crystian/ComfyUI-Crystools.git" "${CUSTOM_NODES_DIR}/ComfyUI-Crystools" "" "de7934df6655497458b2129824b9db31f80cd09f"

# Install Python dependencies only if they haven't been installed before
if [ ! -f "$INSTALL_LOCK_FILE" ]; then
    echo "🐍 First time setup: Installing all custom node dependencies..."

    # Install all packages in a single, controlled command.
    # Note: torch, torchvision, and opencv-python are intentionally excluded
    # to resolve conflicts and enforce the versions from the Dockerfile.
    pip install --no-cache-dir \
        GitPython \
        PyGithub \
        matrix-client==0.4.0 \
        transformers \
        huggingface-hub'>'0.20 \
        typer \
        rich \
        typing-extensions \
        toml \
        uv \
        chardet \
        pillow'>='10.3.0 \
        scipy'>='1.11.4 \
        color-matcher \
        matplotlib \
        mss \
        segment-anything \
        scikit-image \
        piexif \
        numpy==1.26.4 \
        dill \
        git+https://github.com/facebookresearch/sam2 \
        ultralytics \
        importlib_metadata \
        filelock \
        einops \
        pyyaml \
        python-dateutil \
        mediapipe \
        svglib \
        fvcore \
        yapf \
        omegaconf \
        ftfy \
        addict \
        yacs \
        trimesh[easy] \
        albumentations'>='1.4.16 \
        scikit-learn \
        timm \
        peft \
        accelerate'>='0.26.0 \
        insightface==0.7.3 \
        onnx'>='1.14.0 \
        gguf'>='0.13.0 \
        sentencepiece \
        protobuf \
        cython \
        facexlib \
        onnxruntime-gpu \
        deepdiff \
        pynvml \
        py-cpuinfo \
        jetson-stats

    # Impact Pack disabled due to PyTorch 2.2.2 compatibility conflict
    # Requires torch>=2.5.1 — revisit if upgrading base PyTorch in the future
    # Run special installation scripts for specific nodes
    # echo "--- Running installer for Impact Pack ---"
    # python3 "${CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack/install.py"

    echo "--- Running installer for Reactor ---"
    python3 "${CUSTOM_NODES_DIR}/comfyui-reactor-node/install.py"

    # Enforce the correct PyTorch version as the absolute last step
    echo "--- Enforcing final PyTorch version to prevent conflicts ---"
    pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --extra-index-url https://download.pytorch.org/whl/cu122
    # Create the lock file to prevent this block from running again
    touch "$INSTALL_LOCK_FILE"
    echo "✅ Python dependencies installed."
else
    echo "✅ Python dependencies already installed, skipping."
fi

echo "✅ Custom node setup complete."