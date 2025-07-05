FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Install system dependencies
RUN apt update && apt install -y \
    python3 python3-pip git git-lfs wget && \
    git lfs install && \
    apt clean && rm -rf /var/lib/apt/lists/*

# Install PyTorch
RUN pip install --default-timeout=300 --retries=10 torch==2.2.2 torchvision==0.17.2 --extra-index-url https://download.pytorch.org/whl/cu122

# Install ComfyUI
WORKDIR /workspace
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI && \
    cd /workspace/ComfyUI && \
    git checkout 27870ec3c30e56be9707d89a120eb7f0e2836be1

# Install ComfyUI dependencies
RUN pip install --retries=10 -r /workspace/ComfyUI/requirements.txt

# Copy installer + startup
COPY install_maxedout.py /workspace/install_maxedout.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose port
EXPOSE 8188

# Default entrypoint for local Docker (RunPod overrides this)
CMD ["/start.sh"]
