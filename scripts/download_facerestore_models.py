from install_maxedout import download, MODEL_DIR

FILES = [
    ("FaceRestore_Models/codeformer.pth", "facerestore_models/codeformer.pth", "1009e537e0c2a07d4cabce6355f53cb66767cd4b4297ec7a4a64ca4b8a5684b7"),
    ("FaceRestore_Models/GFPGANv1.4.pth", "facerestore_models/GFPGANv1.4.pth", "e2cd4703ab14f4d01fd1383a8a8b266f9a5833dacee8e6a79d3bf21a1b6be5ad"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
