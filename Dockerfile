FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Install system dependencies
RUN apt update && apt install -y \
    python3 python3-pip git git-lfs wget && \
    git lfs install && \
    apt clean && rm -rf /var/lib/apt/lists/*

# Install PyTorch
ARG PYTORCH=2.2.2
ARG TORCHVISION=0.17.2
ARG TORCHAUDIO=2.2.2
ARG CUDA=122

RUN pip install --no-cache-dir --default-timeout=300 --retries=10 \
    torch==${PYTORCH} torchvision==${TORCHVISION} torchaudio==${TORCHAUDIO} \
    --extra-index-url https://download.pytorch.org/whl/cu${CUDA}

# Install ComfyUI
WORKDIR /workspace
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI && \
    cd /workspace/ComfyUI && \
    git checkout 27870ec3c30e56be9707d89a120eb7f0e2836be1

# Create necessary model directories
RUN mkdir -p /workspace/ComfyUI/models/clip \
             /workspace/ComfyUI/models/diffusion_models \
             /workspace/ComfyUI/models/vae

# Install ComfyUI dependencies
RUN pip install --retries=10 -r /workspace/ComfyUI/requirements.txt

# Copy scripts + startup
COPY install_maxedout.py /workspace/install_maxedout.py
COPY download_core_models.py /workspace/download_core_models.py
COPY download_upscale_models.py /workspace/download_upscale_models.py
COPY download_adetailer_models.py /workspace/download_adetailer_models.py
COPY start.sh /workspace/start.sh
RUN chmod +x /start.sh

# Expose port
EXPOSE 8188

# Default entrypoint for local Docker (RunPod overrides this)
CMD ["/start.sh"]
