import os
import sys
from huggingface_hub import hf_hub_download

def download_dermaai():
    repo_id = "Siraja704/DermaAI"
    filename = "DermaAI.keras"
    dest_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model")
    os.makedirs(dest_dir, exist_ok=True)
    
    print(f"Downloading {filename} from {repo_id}...")
    local_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=dest_dir,
        local_dir_use_symlinks=False
    )
    print(f"Model successfully downloaded to: {local_path}")
    size_mb = os.path.getsize(local_path) / (1024 * 1024)
    print(f"File size: {size_mb:.2f} MB")
    return local_path

if __name__ == "__main__":
    download_dermaai()
