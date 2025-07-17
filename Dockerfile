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

# Clone all custom node repositories
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git comfyui-manager && \
    git clone https://github.com/rgthree/rgthree-comfy.git && \
    git clone https://github.com/kijai/ComfyUI-KJNodes.git && \
    git clone https://github.com/Maxed-Out-99/ComfyUI-MaxedOut.git && \
    git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git && \
    git clone https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git && \
    git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    git clone --recursive https://github.com/ssitu/ComfyUI_UltimateSDUpscale.git && \
    git clone https://github.com/kijai/ComfyUI-Florence2.git && \
    git clone https://codeberg.org/Gourieff/comfyui-reactor-node.git && \
    git clone https://github.com/chrisgoringe/cg-use-everywhere.git && \
    git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git && \
    git clone https://github.com/city96/ComfyUI-GGUF.git && \
    git clone https://github.com/kijai/ComfyUI-DepthAnythingV2.git && \
    git clone https://github.com/lldacing/ComfyUI_PuLID_Flux_ll.git && \
    git clone https://github.com/crystian/ComfyUI-Crystools.git

# Install Python dependencies for nodes that have them, one by one.
RUN pip install --no-cache-dir -r comfyui-manager/requirements.txt
# RUN pip install --no-cache-dir -r rgthree-comfy/requirements.txt
# RUN pip install --no-cache-dir -r ComfyUI-KJNodes/requirements.txt
# RUN pip install --no-cache-dir -r ComfyUI-Impact-Pack/requirements.txt
# RUN python3 ComfyUI-Impact-Pack/install.py
# RUN pip install --no-cache-dir -r ComfyUI-Impact-Subpack/requirements.txt
# RUN pip install --no-cache-dir -r comfyui_controlnet_aux/requirements.txt
# RUN pip install --no-cache-dir -r ComfyUI-Florence2/requirements.txt
# RUN pip install --no-cache-dir -r comfyui-reactor-node/requirements.txt
# RUN python3 comfyui-reactor-node/install.py
# RUN pip install --no-cache-dir -r ComfyUI-GGUF/requirements.txt
# RUN pip install --upgrade --no-cache-dir gguf
# RUN pip install --no-cache-dir -r ComfyUI-DepthAnythingV2/requirements.txt
# RUN pip install --no-cache-dir -r ComfyUI_PuLID_Flux_ll/requirements.txt
# RUN pip install --no-cache-dir -r ComfyUI-Crystools/requirements.txt

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
COPY --chmod=755 start.sh /opt/start.sh
COPY --chmod=755 scripts/ /workspace/scripts/
COPY --chmod=644 workflows/ /workspace/ComfyUI/user/default/workflows/
COPY --chmod=644 comfy.settings.json /workspace/ComfyUI/user/default/comfy.settings.json
COPY custom_nodes/ComfyUI-MaxedOut-Runpod /workspace/ComfyUI/custom_nodes/ComfyUI-MaxedOut-Runpod

# Copy Patreon auth files
COPY --chmod=755 auth/app.py /workspace/auth/app.py
COPY --chmod=644 auth/success.html /workspace/auth/success.html
COPY --chmod=644 auth/fail.html /workspace/auth/fail.html
COPY --chmod=644 auth/requirements.txt /workspace/auth/requirements.txt

RUN pip install --no-cache-dir -r /workspace/auth/requirements.txt

# Expose ComfyUI default port
EXPOSE 8188
# Expose Patreon unlock server port
EXPOSE 7860

# Entrypoint
CMD ["/opt/start.sh"]
