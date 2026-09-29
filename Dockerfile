FROM nvidia/cuda:13.3.1-cudnn-runtime-ubuntu24.04

LABEL maintainer="maxedout.ai" \
      version="minimax-h3-v1" \
      description="Runpod-ready ComfyUI image for Turbo and non-Turbo MiniMax H3 10Eros Max Hybrid Beta 5 INT8"

ARG DEBIAN_FRONTEND=noninteractive
ARG COMFYUI_VERSION=v0.37.0
ARG TORCH_VERSION=2.14.0
ARG TORCHVISION_VERSION=0.29.0
ARG TORCHAUDIO_VERSION=2.11.0
ARG MAXEDOUT_NODES_REPO=https://github.com/Maxed-Out-99/ComfyUI-MaxedOut.git
ARG VHS_NODES_REPO=https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
ARG KJ_NODES_REPO=https://github.com/kijai/ComfyUI-KJNodes.git
ARG COMFY_GALLERY_REPO=https://github.com/Maxed-Out-99/ComfyGallery.git
ARG CUSTOM_NODES_CACHE_BUST=manual

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DOWNLOAD_TIMEOUT=60 \
    HF_XET_HIGH_PERFORMANCE=1 \
    PATH="/opt/venv/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        ffmpeg \
        git \
        libgl1 \
        libglib2.0-0 \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv \
    && python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install \
        torch==${TORCH_VERSION} \
        torchvision==${TORCHVISION_VERSION} \
        torchaudio==${TORCHAUDIO_VERSION} \
        --index-url https://download.pytorch.org/whl/cu130

RUN git clone --depth 1 --branch "${COMFYUI_VERSION}" \
        https://github.com/Comfy-Org/ComfyUI.git /opt/ComfyUI \
    && python -m pip install --retries 10 -r /opt/ComfyUI/requirements.txt \
    && python -m pip install "huggingface-hub>=0.34,<2" "hf-xet>=1.1,<2"

COPY --chmod=755 scripts/ /opt/scripts/

RUN echo "[build] Custom-node refresh: ${CUSTOM_NODES_CACHE_BUST}" \
    && git clone --depth 1 "${MAXEDOUT_NODES_REPO}" \
        /opt/ComfyUI/custom_nodes/ComfyUI-MaxedOut \
    && git clone --depth 1 "${VHS_NODES_REPO}" \
        /opt/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite \
    && git clone --depth 1 "${KJ_NODES_REPO}" \
        /opt/ComfyUI/custom_nodes/ComfyUI-KJNodes \
    && git clone --depth 1 "${COMFY_GALLERY_REPO}" \
        /opt/ComfyUI/custom_nodes/ComfyGallery \
    && python /opt/scripts/patch_comfygallery.py \
        /opt/ComfyUI/custom_nodes/ComfyGallery/web/comfy_gallery_button.js \
    && python -m pip install --retries 10 \
        -r /opt/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt \
        -r /opt/ComfyUI/custom_nodes/ComfyUI-KJNodes/requirements.txt \
        -r /opt/ComfyUI/custom_nodes/ComfyGallery/requirements.txt \
    && python -m pip uninstall -y opencv-python \
    && python -m pip install --force-reinstall --no-deps opencv-python-headless \
    && python -m pip check \
    && python -m compileall -q \
        /opt/ComfyUI/custom_nodes/ComfyUI-MaxedOut \
        /opt/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite \
        /opt/ComfyUI/custom_nodes/ComfyUI-KJNodes \
        /opt/ComfyUI/custom_nodes/ComfyGallery \
    && python -c "import color_matcher, cv2, imageio_ffmpeg, matplotlib, mss; from PIL import Image"

COPY --chmod=755 start.sh /opt/start.sh
COPY --chmod=644 comfy.settings.json /opt/comfy.settings.json

EXPOSE 8188 8190

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=5 CMD \
  curl -fsS http://localhost:8188/prompt \
  && curl -fsS http://localhost:8190/api/config \
  || exit 1

CMD ["/opt/start.sh"]
