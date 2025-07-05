FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Install system dependencies
RUN apt update && apt install -y \
    python3 python3-pip git wget && \
    apt clean

# Install PyTorch
RUN pip install --default-timeout=300 --retries=10 \
    torch==2.2.2 torchvision==0.17.2 \
    --extra-index-url https://download.pytorch.org/whl/cu122

# Install ComfyUI at locked commit
WORKDIR /workspace
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    git checkout 27870ec3c30e56be9707d89a120eb7f0e2836be1

# Install ComfyUI dependencies
RUN pip install -r /workspace/ComfyUI/requirements.txt

# --- START: Added from your installer script ---

# Set working directory to ComfyUI
WORKDIR /workspace/ComfyUI

# 1. Install Python dependencies from your script
RUN pip install --use-pep517 facexlib insightface

# 2. Clone the custom nodes repository
RUN git clone https://github.com/Maxed-Out-99/ComfyUI-MaxedOut.git \
    custom_nodes/ComfyUI-MaxedOut

# 3. Download all models into the image
RUN HF_COMMIT="96710c9df25bfc5efddfe8e75b61ad2b71f12108" && \
    BASE_URL="https://huggingface.co/MaxedOut/ComfyUI-Starter-Packs/resolve/$HF_COMMIT" && \
    mkdir -p models/clip models/diffusion_models models/vae models/pulid \
             models/style_models models/clip_vision models/upscale_models \
             models/sams models/ultralytics/bbox models/controlnet \
             models/facerestore_models models/loras && \
    wget -O models/clip/t5xxl_fp16.safetensors "$BASE_URL/Flux1/clip/t5xxl_fp16.safetensors" && \
    wget -O models/clip/clip_l.safetensors "$BASE_URL/Flux1/clip/clip_l.safetensors" && \
    wget -O models/diffusion_models/flux1-dev-fp8.safetensors "$BASE_URL/Flux1/unet/Dev/flux1-dev-fp8.safetensors" && \
    wget -O models/diffusion_models/flux1-schnell-fp8.safetensors "$BASE_URL/Flux1/unet/Schnell/flux1-schnell-fp8.safetensors" && \
    wget -O models/vae/ae.safetensors "$BASE_URL/Flux1/vae/ae.safetensors" && \
    wget -O models/upscale_models/RealESRGAN_x2plus.pth "$BASE_URL/Upscale_Models/RealESRGAN_x2plus.pth" && \
    wget -O models/upscale_models/4x-UltraSharp.pth "$BASE_URL/Upscale_Models/4x-UltraSharp.pth" && \
    wget -O models/loras/navi_flux_v1.safetensors "$BASE_URL/Flux1/LoRas/navi_flux_v1.safetensors"

# Return to the base workspace directory
WORKDIR /workspace

# Create the specific default workflows directory to ensure it exists
RUN mkdir -p /workspace/ComfyUI/user/default/workflows

COPY "workflows/Flux Bootcamp (Level 1).json" /workspace/ComfyUI/user/default/workflows/

# Copy the launch script (make sure you've edited it to remove the installer call)
COPY launch.sh /workspace/launch.sh
RUN chmod +x /workspace/launch.sh

# Expose ComfyUI web port
EXPOSE 8188

# Use bash explicitly instead of JSON array to support env vars and logging
CMD bash /workspace/launch.sh