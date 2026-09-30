# Runpod MiniMax H3 Template

A minimal Runpod/ComfyUI image for **Turbo and non-Turbo MiniMax H3 10Eros Max Hybrid Beta 5 INT8** generation with native audio.

This fork removes the Flux models and workflows, Jupyter/auth service, and Patreon installer. It serves ComfyUI on port `8188`, ComfyGallery on port `8190`, includes the five custom-node repositories listed below, and downloads the five required model files to `/workspace` on first boot. No workflow is bundled.

## Included custom nodes

- [`Maxed-Out-99/ComfyUI-MaxedOut`](https://github.com/Maxed-Out-99/ComfyUI-MaxedOut)
- [`Kosinkadink/ComfyUI-VideoHelperSuite`](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) (VHS)
- [`kijai/ComfyUI-KJNodes`](https://github.com/kijai/ComfyUI-KJNodes)
- [`Maxed-Out-99/ComfyGallery`](https://github.com/Maxed-Out-99/ComfyGallery)
- [`crystian/ComfyUI-Crystools`](https://github.com/crystian/ComfyUI-Crystools) (resource monitor and utility nodes)

All five repositories are intentionally unpinned. Docker clones the current default branch during each image build. Rebuilding the same image tag later can therefore produce different node versions; use a new semantic image tag for each build. VHS, KJNodes, ComfyGallery, and Crystools requirements are installed from their current upstream manifests during the build, and FFmpeg is included in the image.

## Runtime versions

- ComfyUI `v0.37.0` — latest stable release when this template was updated
- PyTorch `2.14.0`
- torchvision `0.29.0`
- torchaudio `2.11.0` maintenance line, compatible with newer PyTorch releases
- CUDA 13.0 PyTorch wheels on the NVIDIA CUDA 13.3.1/cuDNN Ubuntu 24.04 base image

ComfyGallery starts with the container on port `8190`. Its browser button is adjusted during the image build to open the standard Runpod `8190` HTTP proxy; non-Runpod and Desktop behavior is left unchanged.

## What it downloads

| Destination under `ComfyUI/models` | Source | Approx. size | SHA-256 |
|---|---|---:|---|
| `diffusion_models/10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors` | `TenStrip/10Eros-Max` | 20.97 GB | `4dd965496e5b1b83cd13c65cbe7a535b8a4d94ae768a7646b4e336d52c4781cf` |
| `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `Comfy-Org/MiniMax-H3` | 15.70 GB | `35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6` |
| `vae/minimax_h3_video_vae_int8_convrot.safetensors` | `Comfy-Org/MiniMax-H3` | 2.81 GB | `52a2c8c73583c86e4f41cdcce3a6ad0ea562987bc0bf3d60a0cef5f5c8e60c0e` |
| `vae/minimax_h3_audio_vae_fp32.safetensors` | `Comfy-Org/MiniMax-H3` | 0.61 GB | `8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48` |
| `diffusion_models/10Eros_Max_h3_hybrid_beta5_int8.safetensors` | `TenStrip/10Eros-Max` | 20.97 GB | `488e0d51fad9fd6b277b6ebfbe46b3fd44374ff7baa1e3c9dfce58d3a1e5b33c` |

The table is also the download order: Turbo first and non-Turbo last. Total model storage is about **61.0 GB** (decimal), excluding Hugging Face's temporary download cache and generated videos. Revisions and hashes are pinned in `scripts/download_models.py`.

No model weights are included in this repository or Docker image.

## Build

```bash
docker build --platform=linux/amd64 \
  --build-arg CUSTOM_NODES_CACHE_BUST="$(date +%s)" \
  -t maxedout99/runpod-minimax-h3:v1.0.0 .
docker push maxedout99/runpod-minimax-h3:v1.0.0
```

Use an immutable version tag in the Runpod template instead of `latest`.

The included GitHub Actions workflow runs tests, builds `linux/amd64`, refreshes the unpinned custom nodes, and publishes `runpod-minimax-h3:v1.0.<run number>`. Add repository secrets named `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` before using it.

## Runpod template settings

- Container image: `maxedout99/runpod-minimax-h3:v1.0.0` (or your registry/tag)
- HTTP ports: `8188` for ComfyUI and `8190` for ComfyGallery
- Volume mount: `/workspace`
- Container disk: at least `40 GB`
- Persistent volume: at least `100 GB`; `150 GB` is safer for outputs and download staging
- Environment variable `HF_TOKEN`: a Hugging Face token that can access both repositories
- Environment variable `MINIMAX_H3_AUTHORIZED=1`: required acknowledgement of model authorization

A 24 GB GPU and 64 GB or more of system RAM is the practical baseline for this quantized stack. Actual capacity depends on resolution, frame count, and ComfyUI's memory behavior.

## First boot

ComfyUI starts while model downloads continue in the background. You can open your workflow immediately, but generation will fail until all files are present and verified.

The bundled `comfy.settings.json` is copied to `/workspace/ComfyUI/user/default/comfy.settings.json` on a fresh pod. It contains the local ComfyUI appearance, canvas, shortcut, preview, and custom-node settings. An existing settings file is preserved.

- ComfyUI log: `/workspace/logs/comfyui.log`
- ComfyGallery log: `/workspace/logs/comfygallery.log`
- Download log: `/workspace/logs/minimax-h3-models.log`
- Machine-readable state: `/workspace/model-download.status.json`

The downloader resumes cached Hugging Face transfers, verifies every final size and SHA-256, and skips already-valid files. It checks free space before starting and keeps a 5 GiB safety margin. A mismatched existing file is renamed with an `.invalid` suffix before replacement.

Do not share either Runpod proxy URL. This image does not add an authentication layer to ComfyUI or ComfyGallery.

## Persistent-volume upgrades

The image seeds ComfyUI into `/workspace/ComfyUI` only when that directory does not exist. On reused volumes, any missing packaged node repository is added automatically, but an existing node directory is never overwritten. Startup logs warn when persistent copies differ from the image.

When changing the pinned ComfyUI core version, use a fresh volume or deliberately replace `/workspace/ComfyUI` after preserving outputs and user data. The container preserves an existing core checkout rather than silently changing it.

## Authorization and licenses

You are responsible for complying with the model repositories' access terms and licenses. The container refuses to download weights unless `MINIMAX_H3_AUTHORIZED=1` is explicitly set. See `NOTICE` and the upstream model cards before publishing or redistributing an image or generated material.
