import os
import json
import yaml
import numpy as np

class IKSMeaningRetriever:
    def __init__(self, config_path="configs/config.yaml"):
        # Load config
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            
        # Load KB
        self.kb_path = self.config["kb"]["json_path"]
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.kb = json.load(f)
        else:
            self.kb = []
            
        self.model_name = self.config["models"]["sentence_transformer"]
        self.index_path = self.config["kb"]["faiss_index_path"]
        self.model = None
        self.index = None
        self.embeddings = None
        self.index_built = False

    def _initialize_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)

    def build_index(self):
        """
        Builds the FAISS index by embedding the historical meaning and definitions in the KB.
        """
        if not self.kb:
            print("Knowledge Base is empty. Cannot build index.")
            return
            
        self._initialize_model()
        print(f"Building semantic index of KB using {self.model_name}...")
        
        # Build document texts to embed
        # We combine Tamil representation, definition, and historical meaning to capture semantic richness
        self.doc_texts = []
        for entry in self.kb:
            doc_text = f"{entry['tamil']} {entry['concept']} {entry['definition']} {entry['historical_meaning']}"
            self.doc_texts.append(doc_text)
            
        # Encode documents
        self.embeddings = self.model.encode(self.doc_texts, show_progress_bar=False, convert_to_numpy=True)
        
        # L2 normalize for cosine similarity via inner product
        self.embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        
        # Build FAISS index
        try:
            import faiss
            dimension = self.embeddings.shape[1]
            # Use IndexFlatIP for Inner Product (which equals Cosine Similarity on normalized vectors)
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(self.embeddings)
            
            # Save index
            faiss.write_index(self.index, self.index_path)
            print(f"Successfully built and saved FAISS index to {self.index_path}.")
        except ImportError:
            print("FAISS package not found. Falling back to NumPy-based cosine similarity index.")
            self.index = None
            
        self.index_built = True

    def load_index(self):
        """
        Loads the FAISS index if it exists, or builds a new one.
        When a saved FAISS index is found, we skip re-encoding all documents
        (those embeddings are already stored in the index file) and only
        initialize the model for query-time encoding.
        """
        self._initialize_model()
        
        try:
            import faiss
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                # Build doc_texts for reference (no re-encoding needed when using FAISS)
                self.doc_texts = [
                    f"{entry['tamil']} {entry['concept']} {entry['definition']} {entry['historical_meaning']}"
                    for entry in self.kb
                ]
                # Only build numpy embeddings as a fallback if FAISS index failed to load
                self.embeddings = None
                self.index_built = True
                print("FAISS index loaded successfully.")
                return
        except ImportError:
            pass
            
        # If loading fails or FAISS not installed, build it (includes encoding)
        self.build_index()

    def retrieve_candidates(self, query_text, top_k=5):
        """
        Retrieves top K candidate concepts from the KB matching the query text.
        Returns:
            list of dicts containing:
                - concept: name
                - score: similarity score
                - kb_entry: the full KB record
        """
        if not self.kb:
            return []
            
        if not self.index_built:
            self.load_index()
            
        # 1. Search for exact matches in the KB (lexical matches)
        exact_matches = []
        for entry in self.kb:
            if entry["tamil"].strip() == query_text.strip() or entry["concept"].lower() == query_text.lower():
                exact_matches.append({
                    "concept": entry["concept"],
                    "score": 2.0,  # High score to prioritize
                    "kb_entry": entry
                })
                
        # If we have enough exact matches to satisfy top_k, return them
        if len(exact_matches) >= top_k:
            return exact_matches[:top_k]
            
        # 2. Semantic search for remaining candidates
        # Encode query
        query_emb = self.model.encode([query_text], convert_to_numpy=True)
        query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)
        
        semantic_results = []
        
        # Retrieve using FAISS index if available
        if self.index is not None:
            scores, indices = self.index.search(query_emb, top_k)
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.kb) and idx >= 0:
                    semantic_results.append({
                        "concept": self.kb[idx]["concept"],
                        "score": float(score),
                        "kb_entry": self.kb[idx]
                    })
        else:
            # Fallback NumPy Cosine Similarity
            scores = np.dot(self.embeddings, query_emb.T).squeeze(axis=1)
            top_indices = np.argsort(scores)[::-1][:top_k]
            for idx in top_indices:
                semantic_results.append({
                    "concept": self.kb[idx]["concept"],
                    "score": float(scores[idx]),
                    "kb_entry": self.kb[idx]
                })
                
        # Combine and remove duplicates (preserving exact match priority)
        combined = exact_matches + semantic_results
        seen_concepts = set()
        unique_results = []
        for item in combined:
            if item["concept"] not in seen_concepts:
                seen_concepts.add(item["concept"])
                unique_results.append(item)
                
        return unique_results[:top_k]

if __name__ == "__main__":
    # Test execution
    retriever = IKSMeaningRetriever()
    retriever.build_index()
    res = retriever.retrieve_candidates("அறம் செய்ய வேண்டும்", top_k=3)
    print("Candidates retrieved:")
    for r in res:
         print(f" - {r['concept']} (Score: {r['score']:.4f}): {r['kb_entry']['english']}")
