# download_core_models.py

from install_maxedout import download, MODEL_DIR

FILES = [
    ("Flux1/clip/t5xxl_fp16.safetensors", "clip/t5xxl_fp16.safetensors", "6e480b09fae049a72d2a8c5fbccb8d3e92febeb233bbe9dfe7256958a9167635"),
    ("Flux1/clip/clip_l.safetensors", "clip/clip_l.safetensors", "660c6f5b1abae9dc498ac2d21e1347d2abdb0cf6c0c0c8576cd796491d9a6cdd"),
    ("Flux1/unet/Dev/flux1-dev-fp8.safetensors", "diffusion_models/flux1-dev-fp8.safetensors", "1be961341be8f5307ef26c787199f80bf4e0de3c1c0b4617095aa6ee5550dfce"),
    ("Flux1/vae/ae.safetensors", "vae/ae.safetensors", "afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
