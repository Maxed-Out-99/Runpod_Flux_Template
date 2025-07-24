# Base image with CUDA 12.2 and Ubuntu 22.04
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

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
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip tools to known good versions
RUN pip install --no-cache-dir pip==24.0 setuptools==70.0.0 wheel==0.43.0

# Set working directory
WORKDIR /workspace

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI && \
    cd /workspace/ComfyUI && \
    git checkout 27870ec3c30e56be9707d89a120eb7f0e2836be1

# Install ComfyUI base requirements
RUN pip install --no-cache-dir --retries=10 -r /workspace/ComfyUI/requirements.txt

# Install insightface directly
RUN pip install --no-cache-dir insightface==0.7.3
RUN pip install --no-cache-dir --use-pep517 facexlib

# Install PyTorch (with CUDA 12.2 support)
RUN pip install --no-cache-dir torch==${PYTORCH_VERSION} torchvision==${TORCHVISION_VERSION} torchaudio==${PYTORCH_VERSION} --extra-index-url https://download.pytorch.org/whl/cu121

RUN pip install --no-cache-dir \
    invisible-watermark \
    onnx onnxruntime \
    opencv-python

# Force reinstall correct NumPy
RUN pip uninstall -y numpy && pip install --no-cache-dir numpy==1.26.4

# Copy scripts and workflows
COPY --chmod=755 start.sh /opt/start.sh
COPY --chmod=755 scripts/ /workspace/scripts/
COPY --chmod=644 workflows/ /workspace/ComfyUI/user/default/workflows/
COPY --chmod=644 comfy.settings.json /workspace/ComfyUI/user/default/comfy.settings.json
COPY custom_nodes/ComfyUI-MaxedOut-Runpod /workspace/ComfyUI/custom_nodes/ComfyUI-MaxedOut-Runpod

# Copy Patreon auth files
COPY --chmod=755 auth/app.py /workspace/auth/app.py
COPY --chmod=644 auth/success.html /workspace/auth/success.html
COPY --chmod=644 auth/fail.html /workspace/auth/fail.html
COPY --chmod=644 auth/index.html /workspace/auth/index.html
COPY --chmod=644 auth/downloading.html /workspace/auth/downloading.html
COPY --chmod=644 auth/requirements.txt /workspace/auth/requirements.txt

RUN pip install --no-cache-dir -r /workspace/auth/requirements.txt

# Copy the custom node installer script and run it so dependencies are baked in
COPY --chmod=755 install_custom_nodes.sh /opt/install_custom_nodes.sh
RUN /opt/install_custom_nodes.sh

# Expose ComfyUI default port
EXPOSE 8188
# Expose Patreon unlock server port
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD \
  curl -f http://localhost:8188/ || curl -f http://localhost:7860/ || exit 1

# Entrypoint
CMD ["/opt/start.sh"]
