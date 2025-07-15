# Base image with CUDA 12.2 and Ubuntu 22.04
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Set build args for flexibility (optional)
ARG PYTORCH_VERSION=2.2.2
ARG TORCHVISION_VERSION=0.17.2

# Install system dependencies
RUN apt update && apt install -y \
    python3 python3-pip git git-lfs wget curl unzip && \
    git lfs install && \
    apt clean && rm -rf /var/lib/apt/lists/*

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



RUN apt update && apt install -y libgl1 libglib2.0-0 ffmpeg
RUN pip install --no-cache-dir \
    invisible-watermark \
    onnx onnxruntime \
    opencv-python

# Force reinstall correct NumPy
RUN pip uninstall -y numpy && pip install --no-cache-dir numpy==1.26.4

# Install PyTorch (with CUDA 12.2 support)
RUN pip install --no-cache-dir torch==${PYTORCH_VERSION} torchvision==${TORCHVISION_VERSION} --extra-index-url https://download.pytorch.org/whl/cu122

# Clean up pip cache
RUN rm -rf /root/.cache/pip

# Copy scripts and workflows
COPY --chmod=755 start.sh /workspace/start.sh
COPY --chmod=755 scripts/ /workspace/scripts/
COPY --chmod=644 workflows/ /workspace/ComfyUI/user/default/workflows/
COPY --chmod=644 comfy.settings.json /workspace/ComfyUI/user/default/comfy.settings.json
COPY custom_nodes/ComfyUI-MaxedOut-Runpod /workspace/ComfyUI/custom_nodes/ComfyUI-MaxedOut-Runpod

# Copy Patreon auth files
COPY --chmod=755 auth/app.py /workspace/auth/app.py
COPY --chmod=644 auth/success.html /workspace/auth/success.html
COPY --chmod=644 auth/fail.html /workspace/auth/fail.html
COPY --chmod=644 auth/requirements.txt /workspace/auth/requirements.txt

RUN pip install --no-cache-dir -r auth/requirements.txt

# Expose ComfyUI default port
EXPOSE 8188
# Expose Patreon unlock server port
EXPOSE 7860

# Entrypoint
CMD ["/workspace/start.sh"]
