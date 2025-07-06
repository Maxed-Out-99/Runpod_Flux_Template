from install_maxedout import download, BASE_URL, MODEL_DIR

# (URL path on HF, local save path, SHA256 hash)
FILES = [
    ("Upscale_Models/RealESRGAN_x2plus.pth", "upscale_models/RealESRGAN_x2plus.pth", "49fafd45f8fd7aa8d31ab2a22d14d91b536c34494a5cfe31eb5d89c2fa266abb"),
    ("Upscale_Models/4x-UltraSharp.pth", "upscale_models/4x-UltraSharp.pth", "a5812231fc936b42af08a5edba784195495d303d5b3248c24489ef0c4021fe01"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
