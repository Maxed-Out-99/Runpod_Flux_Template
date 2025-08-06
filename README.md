# Flux – ComfyUI RunPod Template

## 🧠 Overview
Welcome to the one-click deployment template for **Flux** on RunPod.  
This setup runs **ComfyUI** with my custom **Flux workflows**, including optional Patreon auth, auto-downloaders, and full 5090 support via CUDA 12.8 + PyTorch Nightly.

---

## 🚀 Features

- **ComfyUI** pinned at commit: `[INSERT COMMIT HASH OR DATE]`
- **Flux Dev UNET** (fp8 by default, fp16 optional)
- **Auto-downloaders** for UNETs, VAEs, LoRAs, etc.
- **Patreon unlock system** (optional via HF_TOKEN)
- **Preinstalled nodes**:
  - `[List major custom nodes, e.g. PulidFluxEvaClipLoader, StyleModelLoader, etc.]`
- **Default workflows included**:
  - `[x] Mega Flux v1`
  - `[ ] Inpainting`
  - `[ ] Outpainting`
  - `[ ] Upscale`
  - `[ ] Image-to-Image`
  - `[ ] Conditioning Variants`
- **JupyterLab** on port 8888 for uploads and file access
- **API support** for automation and remote generation

---

## 🛠️ Getting Started

### 1. Deploy the template  
👉 [Click here to launch on RunPod](https://runpod.io/console/deploy?template=YOUR_TEMPLATE_ID)

### 2. Environment Variables (Optional)
Set these before launching if you want auto-downloads or gated features:

```bash
HF_TOKEN=your_huggingface_token
PATREON_CLIENT_ID=your_id
PATREON_CLIENT_SECRET=your_secret
```

### 3. Network Volume (Optional but Recommended)
If using a RunPod volume:
- Models will persist across pods
- First launch will populate it automatically
- Future launches will be faster

---

## 🧰 API Access

You can queue workflows and poll results using ComfyUI’s HTTP API.

Example usage:

```bash
python api_example.py --ip <YOUR_PUBLIC_IP> --port 8188 --filepath ./workflow.json --prompt "A photorealistic owl wearing sunglasses"
```

You’ll find the IP and port under your pod’s "TCP Port Mappings".

---

## 💻 JupyterLab

Access via port 8888. Token will be printed in the RunPod logs.

**To upload models or files:**
- Click “Connect to HTTP 8888”
- Use the token from logs
- Upload directly or use terminal commands like `wget`

---

## 🧩 Workflow Previews

*(Optional section if you want screenshots)*

| Workflow | Description |
|----------|-------------|
| Mega Flux v1 | General-purpose generation |
| Inpainting | Mask-based editing |
| Outpainting | Scene expansion |
| Conditioning Cascade | Testing prompt stacking |

---

## 📦 Model Download Scripts

Located in `/workspace/scripts/`:

```bash
bash /workspace/scripts/download_all_mega_files.py
bash /workspace/scripts/download_small_mega_files.py
```

Use these if you skip the auto-downloaders.

---

## 🧪 Compatibility Notes

- ✅ Supports **RTX 5090+**
- ✅ Compatible with **3090–4090**
- ✅ Built on CUDA 12.8.1 + PyTorch Nightly (cu128)
- ❌ Not tested on ARM64 (use only x86_64 pods)

---

## 📅 Updates

```
2025-08-05:
- Initial public release of Flux RunPod template
- Includes Mega Flux v1, Patreon unlock, FP8 defaults

2025-08-XX:
- [Add future updates here]
```

---

## 🐇 Faster Deploy (Optional)

Use a trimmed-down version of the template **without bundled models** for faster redeploys:

👉 [Lite Template](https://runpod.io/console/deploy?template=YOUR_LITE_ID)

---

## 🎬 Demo Video (Optional)

[![Watch Demo](https://your-thumbnail-link.png)](https://youtube.com/your-demo-url)

---

## 📄 License

Distributed under the [MIT License](LICENSE)

---

Happy creating!  
— **MaxedOut**
