import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import sys
import time
from huggingface_hub import hf_hub_download

print("Downloading NLLB model weights from hf-mirror.com...")
t0 = time.time()
try:
    path = hf_hub_download(repo_id="facebook/nllb-200-distilled-600M", filename="pytorch_model.bin")
    print(f"Success! Downloaded in {time.time() - t0:.2f} seconds.")
    print("Saved to:", path)
except Exception as e:
    print(f"Error: {e}")
