from install_maxedout import download, MODEL_DIR

FILES = [
    ("Flux1/unet/Canny/flux1-canny-dev-fp8.safetensors", "diffusion_models/flux1-canny-dev-fp8.safetensors", "3225da20cfcf18a0537147acb5f57fa11f75ff568827cadcfcbba3289f136574"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
