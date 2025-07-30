from install_maxedout import download, MODEL_DIR
from pathlib import Path
from tqdm.auto import tqdm

FILES = [
    ("Flux1/unet/Fill/flux1-fill-dev-fp16.safetensors", "diffusion_models/flux1-fill-dev-fp16.safetensors", "03e289f530df51d014f48e675a9ffa2141bc003259bf5f25d75b957e920a41ca"),
    ("Flux1/unet/Canny/flux1-canny-dev-fp16.safetensors", "diffusion_models/flux1-canny-dev-fp16.safetensors", "996876670169591cb412b937fbd46ea14cbed6933aef17c48a2dcd9685c98cdb"),
    ("Flux1/unet/Depth/flux1-depth-dev-fp16.safetensors", "diffusion_models/flux1-depth-dev-fp16.safetensors", "41360d1662f44ca45bc1b665fe6387e91802f53911001630d970a4f8be8dac21"),
    ("Flux1/PuLID/pulid_flux_v0.9.1.safetensors", "pulid/pulid_flux_v0.9.1.safetensors", "92c41c3af322b02e58e1b32842e4601e08c8f16ec1fe80089dbe957df510f51d"),
    ("Flux1/Style_Models/flux1-redux-dev.safetensors", "style_models/flux1-redux-dev.safetensors", "a1b3bdcb4bdc58ce04874b9ca776d61fc3e914bb6beab41efb63e4e2694dca45"),
    ("Flux1/clip_vision/sigclip_vision_patch14_384.safetensors", "clip_vision/sigclip_vision_patch14_384.safetensors", "1fee501deabac72f0ed17610307d7131e3e9d1e838d0363aa3c2b97a6e03fb33"),
    ("Flux1/Controlnets/flux_shakker_labs_union_pro-fp8.safetensors", "controlnet/flux_shakker_labs_union_pro-fp8.safetensors", "9535c82da8b4abb26eaf827e60cc3da401ed676ea85787f17b168a671b27e491"),
]

def main():
    total_files = len(FILES)
    for i, (remote, local, sha256) in enumerate(FILES):
        local_path = MODEL_DIR / local
        
        # Print the overall status for the web UI
        print(f"OVERALL:: [{i + 1}/{total_files}] Now downloading: {local_path.name}")
        
        # Call download with show_progress=False
        download(remote, local_path, sha256, show_progress=False)
    Path("/workspace/logs/download_all.done").touch()

if __name__ == "__main__":
    main()
