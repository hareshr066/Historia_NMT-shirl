import sys
from huggingface_hub import hf_hub_download

repo_id = "facebook/nllb-200-distilled-600M"
required_files = [
    "config.json",
    "generation_config.json",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json"
]

print(f"Downloading required PyTorch metadata files for {repo_id}...")

try:
    for f in required_files:
        print(f"Downloading {f}...")
        path = hf_hub_download(repo_id=repo_id, filename=f)
        print(f" -> Saved to {path}")
    print("\nAll required NLLB metadata files downloaded successfully!")
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()
