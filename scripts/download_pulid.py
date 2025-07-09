from install_maxedout import download, MODEL_DIR

FILES = [
    ("Flux1/PuLID/pulid_flux_v0.9.1.safetensors", "pulid/pulid_flux_v0.9.1.safetensors", "92c41c3af322b02e58e1b32842e4601e08c8f16ec1fe80089dbe957df510f51d"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
