import numpy as np
from backend.ai.embeddings.embedding_model import EmbeddingModelHolder

class IKSMeaningRanker:
    def __init__(self):
        self.model = None

    def _initialize_model(self):
        if self.model is None:
            self.model = EmbeddingModelHolder.get_model()

    def apply_historical_rules(self, sentence_context: str, era: str) -> float:
        """
        Historical Rule Engine:
        Boosts the score of concepts depending on contextual clues in the sentence.
        """
        boost = 0.0
        context_lower = sentence_context.lower()
        
        # Rule 1: Sangam clues
        sangam_clues = ["சங்க", "புறநானூறு", "குறுந்தொகை", "நற்றிணை", "அகநானூறு", "ஐங்குறுநூறு", "பதிற்றுப்பத்து", "பரிபாடல்"]
        if any(clue in context_lower for clue in sangam_clues):
            if era and "Sangam" in era and "Post" not in era:
                boost += 0.2
                
        # Rule 2: Post-Sangam/Kural clues
        post_sangam_clues = ["திருக்குறள்", "குறள்", "அறநெறி", "சிலப்பதிகாரம்", "மணிமேகலை"]
        if any(clue in context_lower for clue in post_sangam_clues):
            if era and "Post-Sangam" in era:
                boost += 0.2
                
        return boost

    def rank_meanings(self, sentence_context: str, candidates: list) -> dict:
        """
        Ranks candidate meanings using semantic similarity, exact match boosts, and rule-based era checks.
        """
        if not candidates:
            return None
            
        self._initialize_model()
        
        candidate_texts = []
        for cand in candidates:
            kb_entry = cand["kb_entry"]
            text = f"{kb_entry['english']} - {kb_entry['definition']} {kb_entry['historical_meaning']}"
            candidate_texts.append(text)
            
        # Encode inputs
        sentence_emb = self.model.encode([sentence_context], convert_to_numpy=True)
        cand_embs = self.model.encode(candidate_texts, convert_to_numpy=True)
        
        # Normalize
        sentence_emb = sentence_emb / np.linalg.norm(sentence_emb, axis=1, keepdims=True)
        cand_embs = cand_embs / np.linalg.norm(cand_embs, axis=1, keepdims=True)
        
        # Cosine similarity
        similarities = np.dot(cand_embs, sentence_emb.T).squeeze(axis=1)
        
        ranked = []
        for i, cand in enumerate(candidates):
            score = float(similarities[i])
            kb_entry = cand["kb_entry"]
            
            # 1. Apply Lexical/Morphological Match Boost
            if cand.get("score", 0) >= 2.0:
                score += 1.0
                
            # 2. Apply Historical Rule Engine Boost
            era_boost = self.apply_historical_rules(sentence_context, kb_entry.get("era", ""))
            score += era_boost
            
            ranked.append({
                "concept": cand["concept"],
                "score": score,
                "kb_entry": kb_entry
            })
            
        # Sort by score descending
        ranked = sorted(ranked, key=lambda x: x["score"], reverse=True)
        
        # Softmax calibrated probability (T=0.1) for confidence metrics
        scores_arr = np.array([r["score"] for r in ranked])
        exp_scores = np.exp((scores_arr - np.max(scores_arr)) / 0.1)
        softmax_probs = exp_scores / np.sum(exp_scores)
        
        top_prob = float(softmax_probs[0])
        
        return {
            "top_concept": ranked[0]["concept"],
            "english_meaning": ranked[0]["kb_entry"]["english"],
            "confidence_percent": round(top_prob * 100, 1),
            "similarity_score": round(ranked[0]["score"], 4),
            "ranked_candidates": ranked
        }
