import numpy
import pandas
import scipy
import sklearn
import huggingface_hub
import torch
import transformers
import sentence_transformers
print("All modules imported successfully!")
from sentence_transformers import SentenceTransformer
print("Class SentenceTransformer imported successfully!")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
print("Model loaded successfully!")
