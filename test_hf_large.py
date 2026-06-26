import sys
import traceback
from huggingface_hub import hf_hub_download

print("Starting HF hub large file download test...")
try:
    repo_id = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    filename = "model.safetensors"
    
    print(f"Downloading {filename} from {repo_id}...")
    local_path = hf_hub_download(repo_id=repo_id, filename=filename)
    print("Download success! Saved to:", local_path)
    
except Exception as e:
    print("An exception occurred during download:")
    traceback.print_exc()
    sys.exit(1)
