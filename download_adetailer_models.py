from install_maxedout import download, BASE_URL, MODEL_DIR

FILES = [
    ("Adetailer/sams/sam_vit_b_01ec64.pth", "sams/sam_vit_b_01ec64.pth", "ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912"),
    ("Adetailer/Ultralytics/bbox/face_yolov8m.pt", "ultralytics/bbox/face_yolov8m.pt", "e3893a92c5c1907136b6cc75404094db767c1e0cfefe1b43e87dad72af2e4c9f"),
    ("Adetailer/Ultralytics/bbox/hand_yolov8s.pt", "ultralytics/bbox/hand_yolov8s.pt", "30878cea9870964d4a238339e9dcff002078bbbaa1a058b07e11c167f67eca1c"),
]

def main():
    for remote, local, sha256 in FILES:
        download(remote, MODEL_DIR / local, sha256)

if __name__ == "__main__":
    main()
