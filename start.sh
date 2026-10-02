#!/usr/bin/env bash
set -Eeuo pipefail

readonly WORKSPACE="${WORKSPACE:-/workspace}"
readonly IMAGE_COMFYUI="/opt/ComfyUI"
readonly COMFYUI_DIR="${COMFYUI_DIR:-${WORKSPACE}/ComfyUI}"
readonly LOG_DIR="${WORKSPACE}/logs"
readonly DOWNLOAD_LOG="${LOG_DIR}/minimax-h3-models.log"
readonly DOWNLOAD_STATUS="${WORKSPACE}/model-download.status.json"
readonly GALLERY_LOG="${LOG_DIR}/comfygallery.log"

mkdir -p "${WORKSPACE}" "${LOG_DIR}"

if [[ ! -d "${COMFYUI_DIR}" ]]; then
  echo "[init] Seeding ComfyUI into ${COMFYUI_DIR}"
  cp -a "${IMAGE_COMFYUI}" "${COMFYUI_DIR}"
fi

readonly -a PACKAGED_NODES=(
  "ComfyUI-MaxedOut"
  "ComfyUI-VideoHelperSuite"
  "ComfyUI-KJNodes"
  "ComfyGallery"
  "ComfyUI-Crystools"
)

mkdir -p "${COMFYUI_DIR}/custom_nodes"

for node_name in "${PACKAGED_NODES[@]}"; do
  source_dir="${IMAGE_COMFYUI}/custom_nodes/${node_name}"
  destination_dir="${COMFYUI_DIR}/custom_nodes/${node_name}"
  if [[ ! -d "${destination_dir}" ]]; then
    echo "[init] Adding packaged custom node: ${node_name}"
    cp -a "${source_dir}" "${destination_dir}"
  elif [[ -d "${source_dir}/.git" && -d "${destination_dir}/.git" ]]; then
    image_revision="$(git -C "${source_dir}" rev-parse HEAD 2>/dev/null || true)"
    volume_revision="$(git -C "${destination_dir}" rev-parse HEAD 2>/dev/null || true)"
    if [[ -n "${image_revision}" && -n "${volume_revision}" && "${image_revision}" != "${volume_revision}" ]]; then
      echo "[warning] ${node_name} on the persistent volume differs from this image; preserving the volume copy"
    fi
  fi
done

image_comfy_revision="$(git -C "${IMAGE_COMFYUI}" rev-parse HEAD 2>/dev/null || true)"
volume_comfy_revision="$(git -C "${COMFYUI_DIR}" rev-parse HEAD 2>/dev/null || true)"
if [[ -n "${image_comfy_revision}" && -n "${volume_comfy_revision}" && "${image_comfy_revision}" != "${volume_comfy_revision}" ]]; then
  echo "[warning] Persistent ComfyUI differs from the image version; preserving /workspace/ComfyUI"
fi

mkdir -p \
  "${COMFYUI_DIR}/models/diffusion_models" \
  "${COMFYUI_DIR}/models/text_encoders" \
  "${COMFYUI_DIR}/models/vae" \
  "${COMFYUI_DIR}/models/background_removal" \
  "${COMFYUI_DIR}/input" \
  "${COMFYUI_DIR}/output" \
  "${COMFYUI_DIR}/temp" \
  "${COMFYUI_DIR}/user/default"

if [[ ! -f "${COMFYUI_DIR}/user/default/comfy.settings.json" ]]; then
  cp /opt/comfy.settings.json "${COMFYUI_DIR}/user/default/comfy.settings.json"
fi

echo "[models] Starting verified MiniMax H3 downloads in the background"
python /opt/scripts/download_models.py \
  --comfy-root "${COMFYUI_DIR}" \
  --status-file "${DOWNLOAD_STATUS}" \
  > >(tee -a "${DOWNLOAD_LOG}") 2>&1 &
DOWNLOAD_PID=$!

cleanup() {
  local exit_code=$?
  if kill -0 "${DOWNLOAD_PID}" 2>/dev/null; then
    kill "${DOWNLOAD_PID}" 2>/dev/null || true
  fi
  if [[ -n "${COMFYUI_PID:-}" ]] && kill -0 "${COMFYUI_PID}" 2>/dev/null; then
    kill "${COMFYUI_PID}" 2>/dev/null || true
  fi
  if [[ -n "${GALLERY_PID:-}" ]] && kill -0 "${GALLERY_PID}" 2>/dev/null; then
    kill "${GALLERY_PID}" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
  exit "${exit_code}"
}
trap cleanup EXIT INT TERM

read -r -a EXTRA_ARGS <<< "${COMFYUI_ARGS:---enable-dynamic-vram}"

echo "[comfyui] Starting on 0.0.0.0:8188"
python "${COMFYUI_DIR}/main.py" \
  --listen 0.0.0.0 \
  --port 8188 \
  "${EXTRA_ARGS[@]}" \
  > "${LOG_DIR}/comfyui.log" 2>&1 &
COMFYUI_PID=$!

echo "[gallery] Starting on 0.0.0.0:8190"
python "${COMFYUI_DIR}/custom_nodes/ComfyGallery/comfy_gallery.py" \
  --no-browser \
  --host 0.0.0.0 \
  --port 8190 \
  --comfyui-path "${COMFYUI_DIR}" \
  --parent-pid "${COMFYUI_PID}" \
  > "${GALLERY_LOG}" 2>&1 &
GALLERY_PID=$!

readonly DEADLINE=$((SECONDS + 180))
until curl -fsS http://127.0.0.1:8188/prompt >/dev/null 2>&1; do
  if ! kill -0 "${COMFYUI_PID}" 2>/dev/null; then
    echo "[comfyui] Process exited before becoming ready"
    tail -n 200 "${LOG_DIR}/comfyui.log" || true
    exit 1
  fi
  if (( SECONDS >= DEADLINE )); then
    echo "[comfyui] Timed out waiting for port 8188"
    tail -n 200 "${LOG_DIR}/comfyui.log" || true
    exit 1
  fi
  sleep 3
done

readonly GALLERY_DEADLINE=$((SECONDS + 90))
until curl -fsS http://127.0.0.1:8190/api/config >/dev/null 2>&1; do
  if ! kill -0 "${GALLERY_PID}" 2>/dev/null; then
    echo "[gallery] Process exited before becoming ready"
    tail -n 200 "${GALLERY_LOG}" || true
    exit 1
  fi
  if (( SECONDS >= GALLERY_DEADLINE )); then
    echo "[gallery] Timed out waiting for port 8190"
    tail -n 200 "${GALLERY_LOG}" || true
    exit 1
  fi
  sleep 2
done

echo "[ready] ComfyUI is available on port 8188"
echo "[ready] ComfyGallery is available on port 8190"
echo "[models] Log: ${DOWNLOAD_LOG}"
echo "[models] Status: ${DOWNLOAD_STATUS}"

wait "${COMFYUI_PID}"
