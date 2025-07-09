from install_maxedout import download, MODEL_DIR

FILES = [
    ("Flux1/unet/Depth/flux1-depth-dev-fp8.safetensors", "diffusion_models/flux1-depth-dev-fp8.safetensors", "4206c6b3f737d350170e2ac9f5b4facf15cb25f1da813608023caf6a34d4edef"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
