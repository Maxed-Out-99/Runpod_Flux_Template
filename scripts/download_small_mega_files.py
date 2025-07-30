from install_maxedout import download, MODEL_DIR
from pathlib import Path
from tqdm.auto import tqdm

FILES = [
    ("Flux1/PuLID/pulid_flux_v0.9.1.safetensors", "pulid/pulid_flux_v0.9.1.safetensors", "92c41c3af322b02e58e1b32842e4601e08c8f16ec1fe80089dbe957df510f51d"),
    ("Flux1/Style_Models/flux1-redux-dev.safetensors", "style_models/flux1-redux-dev.safetensors", "a1b3bdcb4bdc58ce04874b9ca776d61fc3e914bb6beab41efb63e4e2694dca45"),
    ("Flux1/clip_vision/sigclip_vision_patch14_384.safetensors", "clip_vision/sigclip_vision_patch14_384.safetensors", "1fee501deabac72f0ed17610307d7131e3e9d1e838d0363aa3c2b97a6e03fb33"),
]

def main():
    total_files = len(FILES)
    for i, (remote, local, sha256) in enumerate(FILES):
        local_path = MODEL_DIR / local
        
        # Print the overall status for the web UI
        print(f"OVERALL:: [{i + 1}/{total_files}] Now downloading: {local_path.name}")
        
        # Call download with show_progress=False
        download(remote, local_path, sha256, show_progress=False)
        
    Path("/workspace/logs/download_small.done").touch()

if __name__ == "__main__":
    main()
