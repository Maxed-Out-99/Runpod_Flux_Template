FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Install system dependencies
RUN apt update && apt install -y \
    python3 python3-pip git git-lfs wget && \
    git lfs install && \
    apt clean && rm -rf /var/lib/apt/lists/*

# Pre-set working dir
WORKDIR /workspace

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI && \
    cd /workspace/ComfyUI && \
    git checkout 27870ec3c30e56be9707d89a120eb7f0e2836be1

# Install numpy FIRST to match torch's expectations
RUN pip install numpy==1.26.4

# Install PyTorch stack that matches ComfyUI Desktop
ARG TORCH=2.7.0+cu122
ARG TORCHVISION=0.22.0+cu122
RUN pip install \
    torch==${TORCH} \
    torchvision==${TORCHVISION} \
    torchaudio==${TORCHAUDIO} \
    --extra-index-url https://download.pytorch.org/whl/cu122
# Install remaining ComfyUI requirements
RUN pip install --retries=10 -r /workspace/ComfyUI/requirements.txt

# Copy model download scripts
COPY install_maxedout.py /workspace/ComfyUI/install_maxedout.py
COPY download_core_models.py /workspace/ComfyUI/download_core_models.py
COPY download_upscale_models.py /workspace/ComfyUI/download_upscale_models.py
COPY download_adetailer_models.py /workspace/ComfyUI/download_adetailer_models.py
COPY start.sh /workspace/ComfyUI/start.sh
RUN chmod +x /workspace/ComfyUI/start.sh

# Expose default ComfyUI port
EXPOSE 8188

# Entrypoint
CMD ["/workspace/ComfyUI/start.sh"]
