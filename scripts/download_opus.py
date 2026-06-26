import os
import sys
import requests
import warnings
from tqdm import tqdm

# Disable SSL verification warnings
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

files_to_download = [
    "config.json",
    "generation_config.json",
    "metadata.json",
    "pytorch_model.bin",
    "source.spm",
    "target.spm",
    "tokenizer_config.json",
    "vocab.json"
]

repo_url = "https://hf-mirror.com/Helsinki-NLP/opus-mt-mul-en/resolve/main"
output_dir = "models/opus-mt-mul-en"
os.makedirs(output_dir, exist_ok=True)

print("Starting download of Helsinki-NLP/opus-mt-mul-en from mirror...")

for filename in files_to_download:
    url = f"{repo_url}/{filename}"
    out_path = os.path.join(output_dir, filename)
    
    # Check if already fully downloaded
    if os.path.exists(out_path):
        # We can check size if we want to skip
        # For simplicity, skip if file exists and has size > 0
        if os.path.getsize(out_path) > 0:
            if filename != "metadata.json":
                print(f"{filename} already exists, skipping...")
                continue
                
    print(f"Downloading {filename}...")
    try:
        response = requests.get(url, stream=True, verify=False)
        if response.status_code != 200:
            if filename == "metadata.json":
                print(f"Skipping metadata.json (not found / not required)")
                continue
            else:
                print(f"Error: status code {response.status_code} for {filename}")
                sys.exit(1)
                
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 64 # 64 KB chunks
        
        progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)
        with open(out_path, 'wb') as f:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                f.write(data)
        progress_bar.close()
    except Exception as e:
        print(f"Failed to download {filename}: {e}")
        sys.exit(1)
        
print("\nAll model files downloaded successfully to:", output_dir)
