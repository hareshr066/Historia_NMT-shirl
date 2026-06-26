import time

print("1. Importing torch...")
t = time.time()
import torch
print(f"Done in {time.time() - t:.2f}s.")

print("2. Importing transformers...")
t = time.time()
import transformers
print(f"Done in {time.time() - t:.2f}s.")

print("3. Importing sentence_transformers...")
t = time.time()
import sentence_transformers
print(f"Done in {time.time() - t:.2f}s.")

print("4. Importing SentenceTransformer...")
from sentence_transformers import SentenceTransformer
print("Done.")

print("5. Loading model...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
print("Model loaded successfully!")
