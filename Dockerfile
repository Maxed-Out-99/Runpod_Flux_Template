# Base image with CUDA 12.1 and Ubuntu 22.04
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

LABEL maintainer="maxedout.ai" \
      version="flux-v1" \
      description="RunPod-ready container for ComfyUI + Patreon-auth + Flux"

ENV PYTHONUNBUFFERED=1

# Set build args for flexibility
ARG PYTORCH_VERSION=2.5.1
ARG TORCHVISION_VERSION=0.20.1

# Install system dependencies
RUN apt update && apt install -y \
    python3 python3-pip git git-lfs wget curl unzip && \
    git lfs install && \
    apt clean && rm -rf /var/lib/apt/lists/*


COPY requirements.freeze.txt /tmp/requirements.freeze.txt

RUN pip install --no-cache-dir -r /tmp/requirements.freeze.txt

# Install build tools for insightface & others
RUN apt update && apt install -y \
    build-essential \
    cmake \
    libgl1 \
    ffmpeg \
    ninja-build \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip tools to known good versions
RUN pip install --no-cache-dir pip==24.0 setuptools==70.0.0 wheel==0.43.0

# Add Jupyter Notebook
RUN pip3 install jupyterlab

# Set working directory
WORKDIR /workspace

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI && \
    cd /opt/ComfyUI && \
    git checkout aebac221937b511d46fe601656acdc753435b849

# Install ComfyUI base requirements
RUN pip install --no-cache-dir --retries=10 -r /opt/ComfyUI/requirements.txt

# Install PyTorch (with CUDA 12.1 support)
RUN pip install --no-cache-dir \
    torch==${PYTORCH_VERSION} \
    torchvision==${TORCHVISION_VERSION} \
    torchaudio==${PYTORCH_VERSION} \
    --index-url https://download.pytorch.org/whl/cu121

# Install insightface directly
RUN pip install --no-cache-dir insightface==0.7.3
RUN pip install --no-cache-dir --use-pep517 facexlib

RUN pip install --no-cache-dir \
    invisible-watermark \
    onnx onnxruntime \
    opencv-python==4.12.0.88

# Reinstall correct NumPy
RUN pip uninstall -y numpy && pip install --no-cache-dir numpy==1.26.4

# Copy scripts and workflows
COPY --chmod=755 start.sh /opt/start.sh
COPY --chmod=755 workflows/ /opt/ComfyUI/user/default/workflows/
COPY --chmod=644 comfy.settings.json /opt/ComfyUI/user/default/comfy.settings.json
COPY --chmod=755 custom_nodes/ComfyUI-MaxedOut-Runpod /opt/ComfyUI/custom_nodes/ComfyUI-MaxedOut-Runpod

# Copy scripts nodes
COPY --chmod=755 scripts/ /opt/scripts/

# Copy Patreon auth files
COPY --chmod=755 auth/app.py /opt/auth/app.py
COPY --chmod=644 auth/success.html /opt/auth/success.html
COPY --chmod=644 auth/fail.html /opt/auth/fail.html
COPY --chmod=644 auth/index.html /opt/auth/index.html
COPY --chmod=644 auth/downloading.html /opt/auth/downloading.html
COPY --chmod=644 auth/requirements.txt /opt/auth/requirements.txt
COPY --chmod=644 auth/images/mega_exclusives.jpg /opt/auth/images/mega_exclusives.jpg
COPY auth/public.pem /opt/auth/public.pem



RUN pip install --no-cache-dir -r /opt/auth/requirements.txt

# Copy the custom node installer script and run it so dependencies are baked in
COPY --chmod=755 install_custom_nodes.sh /opt/install_custom_nodes.sh

# Expose ComfyUI default port
EXPOSE 8188
# Expose Patreon unlock server port
EXPOSE 7860
# Expose JupyterLab port
EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD \
  curl -fsS http://localhost:8188/queue/status || exit 1

# Entrypoint
CMD ["/opt/start.sh"]
