# download_core_models.py

from install_maxedout import download, MODEL_DIR

FILES = [
    ("Flux1/clip/t5xxl_fp16.safetensors", "clip/t5xxl_fp16.safetensors", "6e480b09fae049a72d2a8c5fbccb8d3e92febeb233bbe9dfe7256958a9167635"),
    ("Flux1/clip/clip_l.safetensors", "clip/clip_l.safetensors", "660c6f5b1abae9dc498ac2d21e1347d2abdb0cf6c0c0c8576cd796491d9a6cdd"),
    ("Flux1/unet/Dev/flux1-dev-fp8.safetensors", "diffusion_models/flux1-dev-fp8.safetensors", "1be961341be8f5307ef26c787199f80bf4e0de3c1c0b4617095aa6ee5550dfce"),
    ("Flux1/vae/ae.safetensors", "vae/ae.safetensors", "afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38"),
    ("Upscale_Models/RealESRGAN_x2plus.pth", "upscale_models/RealESRGAN_x2plus.pth", "49fafd45f8fd7aa8d31ab2a22d14d91b536c34494a5cfe31eb5d89c2fa266abb"),
    ("Upscale_Models/4x-UltraSharp.pth", "upscale_models/4x-UltraSharp.pth", "a5812231fc936b42af08a5edba784195495d303d5b3248c24489ef0c4021fe01"),
    ("Adetailer/sams/sam_vit_b_01ec64.pth", "sams/sam_vit_b_01ec64.pth", "ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912"),
    ("Adetailer/Ultralytics/bbox/face_yolov8m.pt", "ultralytics/bbox/face_yolov8m.pt", "e3893a92c5c1907136b6cc75404094db767c1e0cfefe1b43e87dad72af2e4c9f"),
    ("Adetailer/Ultralytics/bbox/hand_yolov8s.pt", "ultralytics/bbox/hand_yolov8s.pt", "30878cea9870964d4a238339e9dcff002078bbbaa1a058b07e11c167f67eca1c"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
