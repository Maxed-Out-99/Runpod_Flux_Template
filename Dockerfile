# Base image
FROM nvidia/cuda:12.8.1-runtime-ubuntu22.04


LABEL maintainer="maxedout.ai" \
      version="flux-v1" \
      description="RunPod-ready container for ComfyUI + Patreon-auth + Flux"

ENV PYTHONUNBUFFERED=1

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
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI && \
    cd /workspace/ComfyUI && \
    git checkout aebac221937b511d46fe601656acdc753435b849

# Install ComfyUI base requirements
RUN pip install --no-cache-dir --retries=10 -r /workspace/ComfyUI/requirements.txt

# Install latest PyTorch nightlies with CUDA 12.8 support (for 5090 compatibility)
RUN pip install --no-cache-dir --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# Install insightface directly
RUN pip install --no-cache-dir insightface==0.7.3
RUN pip install --no-cache-dir --use-pep517 facexlib

RUN pip install --no-cache-dir \
    invisible-watermark \
    onnx onnxruntime \
    opencv-python

# Reinstall correct NumPy
RUN pip uninstall -y numpy && pip install --no-cache-dir numpy==1.26.4

# Copy scripts and workflows
COPY --chmod=755 start.sh /workspace/start.sh
COPY --chmod=755 workflows/ /workspace/ComfyUI/user/default/workflows/
COPY --chmod=644 comfy.settings.json /workspace/ComfyUI/user/default/comfy.settings.json
COPY --chmod=755 custom_nodes/ComfyUI-MaxedOut-Runpod /workspace/ComfyUI/custom_nodes/ComfyUI-MaxedOut-Runpod

# Copy scripts nodes
COPY --chmod=755 scripts/ /workspace/scripts/

# Copy Patreon auth files
COPY --chmod=755 auth/app.py /workspace/auth/app.py
COPY --chmod=644 auth/success.html /workspace/auth/success.html
COPY --chmod=644 auth/fail.html /workspace/auth/fail.html
COPY --chmod=644 auth/index.html /workspace/auth/index.html
COPY --chmod=644 auth/downloading.html /workspace/auth/downloading.html
COPY --chmod=644 auth/requirements.txt /workspace/auth/requirements.txt
COPY --chmod=644 auth/images/mega_exclusives.jpg /workspace/auth/images/mega_exclusives.jpg


RUN pip install --no-cache-dir -r /workspace/auth/requirements.txt

# Copy the custom node installer script and run it so dependencies are baked in
COPY --chmod=755 install_custom_nodes.sh /opt/install_custom_nodes.sh
RUN /opt/install_custom_nodes.sh

# Expose ComfyUI default port
EXPOSE 8188
# Expose Patreon unlock server port
EXPOSE 7860
# Expose JupyterLab port
EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD \
  curl -f http://localhost:8188/ || curl -f http://localhost:7860/ || curl -f http://localhost:8888/ || exit 1

# Entrypoint
CMD ["/workspace/start.sh"]
