from install_maxedout import download, MODEL_DIR

FILES = [
    ("Flux1/Style_Models/flux1-redux-dev.safetensors", "style_models/flux1-redux-dev.safetensors", "a1b3bdcb4bdc58ce04874b9ca776d61fc3e914bb6beab41efb63e4e2694dca45"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
