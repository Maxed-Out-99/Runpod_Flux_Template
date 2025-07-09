from install_maxedout import download, MODEL_DIR

FILES = [
    ("Flux1/Controlnets/flux_shakker_labs_union_pro-fp8.safetensors", "controlnet/flux_shakker_labs_union_pro-fp8.safetensors", "9535c82da8b4abb26eaf827e60cc3da401ed676ea85787f17b168a671b27e491"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
