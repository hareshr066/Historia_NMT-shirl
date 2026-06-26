import sys
import os

print("Starting download test...")
print("Python executable:", sys.executable)
print("Current directory:", os.getcwd())

print("Importing sentence_transformers...")
from sentence_transformers import SentenceTransformer

print("Loading paraphrase-multilingual-MiniLM-L12-v2...")
# Force downloading with local_files_only=False and trace progress
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
print("Model loaded successfully!")
print("Model details:", model)
