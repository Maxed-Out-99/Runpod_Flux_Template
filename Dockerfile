FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Install system dependencies
RUN apt update && apt install -y \
    python3 python3-pip git wget && \
    apt clean

# Install PyTorch
RUN pip install --default-timeout=300 --retries=10 torch==2.2.2 torchvision==0.17.2 --extra-index-url https://download.pytorch.org/whl/cu122

# Install ComfyUI
WORKDIR /workspace
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI && \
    cd /workspace/ComfyUI && \
    git checkout 27870ec3c30e56be9707d89a120eb7f0e2836be1

# Install ComfyUI dependencies
RUN pip install -r /workspace/ComfyUI/requirements.txt

# Copy the Maxed Out Installer Script
COPY install_maxedout.py /workspace/install_maxedout.py
COPY launch.sh /workspace/launch.sh
RUN chmod +x /workspace/launch.sh

# Expose port for ComfyUI web UI
EXPOSE 8188

CMD ["/workspace/launch.sh"]
