import sys
from huggingface_hub import hf_hub_download

repo_id = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
required_files = [
    "config.json",
    "config_sentence_transformers.json",
    "model.safetensors",
    "modules.json",
    "sentence_bert_config.json",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "unigram.json",
    "1_Pooling/config.json"
]

print(f"Downloading required PyTorch files for {repo_id}...")

try:
    for f in required_files:
        print(f"Downloading {f}...")
        path = hf_hub_download(repo_id=repo_id, filename=f)
        print(f" -> Saved to {path}")
    print("\nAll required PyTorch model files downloaded successfully!")
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()
