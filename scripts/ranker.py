import yaml
import numpy as np

class IKSMeaningRanker:
    def __init__(self, config_path="configs/config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.model_name = self.config["models"]["sentence_transformer"]
        self.model = None

    def _initialize_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)

    def rank_meanings(self, sentence_context, candidates):
        """
        Ranks candidate meanings using semantic similarity against the full sentence context.
        Args:
            sentence_context (str): The full input sentence (usually Tamil).
            candidates (list): List of candidate dicts from retriever (each having 'concept', 'kb_entry').
        Returns:
            dict containing:
                - top_concept: the best matched concept
                - english_meaning: English meaning of top concept
                - confidence_percent: confidence score as percentage
                - ranked_candidates: sorted list of candidates with updated ranking scores
        """
        if not candidates:
            return None
            
        self._initialize_model()
        
        # Prepare target candidate texts to compare with sentence context.
        # We combine english translation, definition, and historical meaning to give rich semantic context.
        candidate_texts = []
        for cand in candidates:
            kb_entry = cand["kb_entry"]
            text = f"{kb_entry['english']} - {kb_entry['definition']} {kb_entry['historical_meaning']}"
            candidate_texts.append(text)
            
        # Encode sentence context and candidates
        sentence_emb = self.model.encode([sentence_context], convert_to_numpy=True)
        cand_embs = self.model.encode(candidate_texts, convert_to_numpy=True)
        
        # L2 normalize
        sentence_emb = sentence_emb / np.linalg.norm(sentence_emb, axis=1, keepdims=True)
        cand_embs = cand_embs / np.linalg.norm(cand_embs, axis=1, keepdims=True)
        
        # Calculate cosine similarity (inner product)
        similarities = np.dot(cand_embs, sentence_emb.T).squeeze(axis=1)
        
        # Add scores to candidates and sort
        ranked = []
        for i, cand in enumerate(candidates):
            score = float(similarities[i])
            
            # Boost exact matches (marked by retrieval score >= 2.0)
            if cand.get("score", 0) >= 2.0:
                score += 1.0
                
            ranked.append({
                "concept": cand["concept"],
                "score": score,
                "kb_entry": cand["kb_entry"]
            })
            
        # Sort descending by score
        ranked = sorted(ranked, key=lambda x: x["score"], reverse=True)
        
        # Calculate confidence percentage
        # We can use a softmax over scores to represent relative confidence, or directly scale the top cosine similarity.
        # Cosine similarity for multilingual sentence embeddings usually ranges from 0.3 to 0.9.
        # Let's use a calibrated softmax with a temperature parameter (T=0.1) to give clear separation.
        scores = np.array([r["score"] for r in ranked])
        # Shift scores for numerical stability
        exp_scores = np.exp((scores - np.max(scores)) / 0.1)
        softmax_probs = exp_scores / np.sum(exp_scores)
        
        top_prob = float(softmax_probs[0])
        
        return {
            "top_concept": ranked[0]["concept"],
            "english_meaning": ranked[0]["kb_entry"]["english"],
            "confidence_percent": round(top_prob * 100, 1),
            "similarity_score": round(ranked[0]["score"], 4),
            "ranked_candidates": ranked
        }

if __name__ == "__main__":
    # Test code
    from retriever import IKSMeaningRetriever
    retriever = IKSMeaningRetriever()
    retriever.load_index()
    
    sentence = "அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்."
    cands = retriever.retrieve_candidates("அறம்", top_k=3)
    
    ranker = IKSMeaningRanker()
    res = ranker.rank_meanings(sentence, cands)
    print(f"Sentence: {sentence}")
    print(f"Top Concept: {res['top_concept']}")
    print(f"Meaning: {res['english_meaning']}")
    print(f"Confidence: {res['confidence_percent']}%")
