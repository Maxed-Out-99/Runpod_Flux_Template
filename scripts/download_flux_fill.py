from install_maxedout import download, MODEL_DIR

FILES = [
    ("Flux1/unet/Fill/flux1-fill-dev-fp8.safetensors", "diffusion_models/flux1-fill-dev-fp8.safetensors", "0320d505ca42bca99c5bd600b1839ced2b2e980ea985917965d411d98a710729"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
