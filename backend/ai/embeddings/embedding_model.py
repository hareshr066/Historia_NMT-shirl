import os
# Set OpenMP variable to bypass potential DLL duplication warnings
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Safeguard import order
import numpy
import pandas
import scipy
import sklearn

from sentence_transformers import SentenceTransformer
from backend.core.config import SENTENCE_TRANSFORMER_MODEL

class EmbeddingModelHolder:
    _instance = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        if cls._instance is None:
            print(f"Loading embedding model: {SENTENCE_TRANSFORMER_MODEL}...")
            cls._instance = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
            print("Embedding model loaded successfully.")
        return cls._instance
