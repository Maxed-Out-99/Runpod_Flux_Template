# download_core_models.py

from install_maxedout import download, MODEL_DIR

FILES = [
    ("Flux1/unet/Fill/flux1-fill-dev-fp8.safetensors", "diffusion_models/flux1-fill-dev-fp8.safetensors", "0320d505ca42bca99c5bd600b1839ced2b2e980ea985917965d411d98a710729"),
    ("Flux1/unet/Canny/flux1-canny-dev-fp8.safetensors", "diffusion_models/flux1-canny-dev-fp8.safetensors", "3225da20cfcf18a0537147acb5f57fa11f75ff568827cadcfcbba3289f136574"),
    ("Flux1/unet/Depth/flux1-depth-dev-fp8.safetensors", "diffusion_models/flux1-depth-dev-fp8.safetensors", "4206c6b3f737d350170e2ac9f5b4facf15cb25f1da813608023caf6a34d4edef"),
    ("Flux1/PuLID/pulid_flux_v0.9.1.safetensors", "pulid/pulid_flux_v0.9.1.safetensors", "92c41c3af322b02e58e1b32842e4601e08c8f16ec1fe80089dbe957df510f51d"),
    ("Flux1/Style_Models/flux1-redux-dev.safetensors", "style_models/flux1-redux-dev.safetensors", "a1b3bdcb4bdc58ce04874b9ca776d61fc3e914bb6beab41efb63e4e2694dca45"),
    ("Flux1/clip_vision/sigclip_vision_patch14_384.safetensors", "clip_vision/sigclip_vision_patch14_384.safetensors", "1fee501deabac72f0ed17610307d7131e3e9d1e838d0363aa3c2b97a6e03fb33"),
    ("Flux1/PuLID/pulid_flux_v0.9.1.safetensors", "pulid/pulid_flux_v0.9.1.safetensors", "92c41c3af322b02e58e1b32842e4601e08c8f16ec1fe80089dbe957df510f51d"),
    ("Flux1/Style_Models/flux1-redux-dev.safetensors", "style_models/flux1-redux-dev.safetensors", "a1b3bdcb4bdc58ce04874b9ca776d61fc3e914bb6beab41efb63e4e2694dca45"),
    ("Flux1/clip_vision/sigclip_vision_patch14_384.safetensors", "clip_vision/sigclip_vision_patch14_384.safetensors", "1fee501deabac72f0ed17610307d7131e3e9d1e838d0363aa3c2b97a6e03fb33"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
