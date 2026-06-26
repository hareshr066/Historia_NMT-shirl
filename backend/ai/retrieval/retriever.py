import os
import json
import numpy as np
import faiss
from backend.core.config import KB_JSON_PATH, KB_INDEX_PATH
from backend.ai.embeddings.embedding_model import EmbeddingModelHolder

class IKSMeaningRetriever:
    def __init__(self):
        self.kb_path = KB_JSON_PATH
        self.index_path = KB_INDEX_PATH
        self.model = None
        self.index = None
        self.embeddings = None
        self.index_built = False
        self.reload_kb()

    def reload_kb(self):
        """Loads/Reloads the Knowledge Base from the database, falling back to the JSON file if empty."""
        try:
            from backend.core.database import SessionLocal
            from backend.core.models import Concept
            
            db = SessionLocal()
            db_concepts = db.query(Concept).all()
            if db_concepts:
                self.kb = []
                for c in db_concepts:
                    self.kb.append({
                        "id": c.id,
                        "concept": c.concept,
                        "tamil": c.tamil,
                        "romanization": c.romanization or c.concept,
                        "language": c.language or "Tamil",
                        "english": c.english_meaning,
                        "era": c.era or "Classical",
                        "definition": c.definition or "",
                        "historical_meaning": c.historical_meaning or "",
                        "modern_meaning": c.modern_meaning or "",
                        "commentary": c.commentary or "",
                        "source_reference": c.source_reference or "Tolkappiyam & Literature",
                        "confidence": c.confidence if c.confidence is not None else 1.0,
                        "verified_by": c.verified_by or "Tamil Scholar / IKS Researcher",
                        "revision_history": c.revision_history or "[]",
                        "version": c.version or 1
                    })
                db.close()
                print(f"Retriever: Successfully loaded {len(self.kb)} concepts from SQL database.")
                return
            db.close()
        except Exception as e:
            print(f"Retriever: Database query failed or empty ({e}). Falling back to JSON file.")

        # Fallback to loading static JSON file
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.kb = json.load(f)
            # Standardize keys to match database schema
            for entry in self.kb:
                if "english" not in entry and "english_meaning" in entry:
                    entry["english"] = entry["english_meaning"]
                elif "english" in entry and "english_meaning" not in entry:
                    entry["english_meaning"] = entry["english"]
                if "romanization" not in entry:
                    entry["romanization"] = entry["concept"]
                if "language" not in entry:
                    entry["language"] = "Tamil"
                if "commentary" not in entry:
                    entry["commentary"] = entry.get("historical_meaning", "")
                if "verified_by" not in entry:
                    entry["verified_by"] = "Tamil Scholar / IKS Researcher"
                if "version" not in entry:
                    entry["version"] = 1
                if "revision_history" not in entry:
                    entry["revision_history"] = "[]"
        else:
            self.kb = []

    def _initialize_model(self):
        if self.model is None:
            self.model = EmbeddingModelHolder.get_model()

    def build_index(self):
        """Builds the FAISS index by embedding the historical meaning and definitions in the KB."""
        if not self.kb:
            print("Knowledge Base is empty. Cannot build index.")
            return
            
        self._initialize_model()
        print("Building semantic index of KB...")
        
        self.doc_texts = []
        for entry in self.kb:
            doc_text = f"{entry['tamil']} {entry['concept']} {entry['definition']} {entry['historical_meaning']}"
            self.doc_texts.append(doc_text)
            
        self.embeddings = self.model.encode(self.doc_texts, show_progress_bar=False, convert_to_numpy=True)
        self.embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings)
        
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        print(f"Successfully built and saved FAISS index to {self.index_path}.")
        self.index_built = True

    def load_index(self):
        """Loads the FAISS index if it exists, or builds a new one."""
        self._initialize_model()
        
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                # Load docs and compute embeddings for fallback checks
                self.doc_texts = [f"{entry['tamil']} {entry['concept']} {entry['definition']} {entry['historical_meaning']}" for entry in self.kb]
                self.embeddings = self.model.encode(self.doc_texts, show_progress_bar=False, convert_to_numpy=True)
                self.embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
                self.index_built = True
                print("FAISS index loaded successfully.")
                return
            except Exception as e:
                print(f"Error loading index: {e}. Rebuilding...")
                
        self.build_index()

    def normalize_tamil_word(self, word: str) -> str:
        """
        Applies morphological rule-based normalization to strip Tamil agglutinative suffixes.
        Covers 50+ common IKS concept root mappings.
        E.g. "அறத்தின்" / "அறத்தை" -> "அறம்"
             "அன்பிலார்" / "அன்புடையார்" -> "அன்பு"
             "அருட்செல்வம்" -> "அருள்"
        """
        word = word.strip()
        if not word:
            return ""

        # Core philosophical values
        if word.startswith("அற"):
            return "அறம்"
        if word.startswith("அன்ப"):
            return "அன்பு"
        if word.startswith("அருள்") or word.startswith("அருட்"):
            return "அருள்"
        if word.startswith("ஊழி") or word.startswith("ஊழ்"):
            return "ஊழ்"
        if word.startswith("தவ"):
            return "தவம்"
        if word.startswith("இன்ப"):
            return "இன்பம்"
        if word.startswith("புகழ்") or word.startswith("புகழ"):
            return "புகழ்"
        if word.startswith("பொருள்") or word.startswith("பொரு"):
            return "பொருள்"

        # Thirukkural virtues
        if word.startswith("ஒழுக்க"):
            return "ஒழுக்கம்"
        if word.startswith("வாய்மை") or word.startswith("வாய்ம"):
            return "வாய்மை"
        if word.startswith("கொல்லாமை") or word.startswith("கொல்லா"):
            return "கொல்லாமை"
        if word.startswith("ஈகை") or word.startswith("ஈக"):
            return "ஈகை"
        if word.startswith("கொடை") or word.startswith("கொடு"):
            return "கொடை"
        if word.startswith("மானம்") or word.startswith("மான"):
            return "மானம்"
        if word.startswith("நாண்") or word.startswith("நாண"):
            return "நாண்"
        if word.startswith("கற்ப") or word.startswith("கற்பு"):
            return "கற்பு"
        if word.startswith("விருந்த") or word.startswith("விருந்தோம்"):
            return "விருந்தோம்பல்"
        if word.startswith("வீர"):
            return "வீரம்"
        if word.startswith("செங்கோல்") or word.startswith("செங்கோ"):
            return "செங்கோல்"

        # Tinai landscapes
        if word.startswith("குறிஞ்சி") or word.startswith("குறிஞ்"):
            return "குறிஞ்சி"
        if word.startswith("முல்லை") or word.startswith("முல்ல"):
            return "முல்லை"
        if word.startswith("மருதம்") or word.startswith("மருத"):
            return "மருதம்"
        if word.startswith("நெய்தல்") or word.startswith("நெய்த"):
            return "நெய்தல்"
        if word.startswith("பாலை") or word.startswith("பாலை"):
            return "பாலை"

        # Social roles & literary concepts
        if word.startswith("சான்றோ"):
            return "சான்றோர்"
        if word.startswith("பண்ப"):
            return "பண்பு"
        if word.startswith("கேளிர்") or word.startswith("கேளி") or word.startswith("கேளு"):
            return "கேளிர்"
        if word.startswith("இல்லற") or word.startswith("இல்வாழ்"):
            return "இல்லறம்"
        if word.startswith("துறவற") or word.startswith("துறவ"):
            return "துறவறம்"
        if word.startswith("தோழி"):
            return "தோழி"
        if word.startswith("வள்ளல்") or word.startswith("வள்ளன"):
            return "வள்ளல்"
        if word.startswith("காதல்") or word.startswith("காதல"):
            return "காதல்"
        if word.startswith("களவு"):
            return "களவு"
        if word.startswith("பிரிவு") or word.startswith("பிரி"):
            return "பிரிவு"
        if word.startswith("கூடல்") or word.startswith("கூட"):
            return "கூடல்"
        if word.startswith("ஊடல்") or word.startswith("ஊட"):
            return "ஊடல்"

        # Warfare genres
        if word.startswith("தும்பை"):
            return "தும்பை"
        if word.startswith("வாகை"):
            return "வாகை"
        if word.startswith("வெட்சி"):
            return "வெட்சி"
        if word.startswith("வஞ்சி"):
            return "வஞ்சி"

        # Instruments & arts
        if word.startswith("யாழ்") or word.startswith("யாழி"):
            return "யாழ்"
        if word.startswith("கூத்த"):
            return "கூத்து"

        # Kinship
        if word.startswith("கணவ"):
            return "கணவன்"
        if word.startswith("மனைவி") or word.startswith("மனை"):
            return "மனைவி"
        if word.startswith("உயிர்") or word.startswith("உயிர"):
            return "உயிர்"
        if word.startswith("வினை"):
            return "வினை"

        return word

    def retrieve_candidates(self, query_text: str, top_k: int = 5) -> list:
        """
        Retrieves candidate concepts using a 3-tier Hybrid Retrieval Pipeline:
        1. Exact Lexical Match (score=2.0, tier='lexical_exact')
        2. Morphological Suffix Stripping (score=1.5, tier='morphological')
        3. Substring Containment (score=1.2, tier='substring')
        4. FAISS Semantic Search (score=cosine, tier='semantic_faiss')
        Plus: Related Concept Cross-Retrieval for high-confidence hits.
        """
        if not self.kb:
            return []

        if not self.index_built:
            self.load_index()

        exact_matches = []
        normalized_query = self.normalize_tamil_word(query_text)
        query_stripped = query_text.strip()
        query_lower = query_text.lower().strip()
        norm_lower = normalized_query.lower()

        seen_concepts = set()

        # Tier 1: Exact Lexical & Morphological pass
        for entry in self.kb:
            entry_tamil = entry["tamil"].strip()
            entry_concept = entry["concept"].lower()

            if entry_tamil == query_stripped or entry_concept == query_lower:
                # Exact match
                cand = {
                    "concept": entry["concept"],
                    "score": 2.0,
                    "match_tier": "lexical_exact",
                    "kb_entry": entry
                }
                if entry["concept"] not in seen_concepts:
                    seen_concepts.add(entry["concept"])
                    exact_matches.append(cand)
            elif entry_tamil == normalized_query or entry_concept == norm_lower:
                # Morphological root match
                cand = {
                    "concept": entry["concept"],
                    "score": 1.5,
                    "match_tier": "morphological",
                    "kb_entry": entry
                }
                if entry["concept"] not in seen_concepts:
                    seen_concepts.add(entry["concept"])
                    exact_matches.append(cand)
            elif (len(query_stripped) >= 3 and entry_tamil.startswith(query_stripped[:3])):
                # Substring / prefix containment (agglutinative partial match)
                cand = {
                    "concept": entry["concept"],
                    "score": 1.2,
                    "match_tier": "substring",
                    "kb_entry": entry
                }
                if entry["concept"] not in seen_concepts:
                    seen_concepts.add(entry["concept"])
                    exact_matches.append(cand)

        if len(exact_matches) >= top_k:
            result = exact_matches[:top_k]
            # Cross-retrieve related concepts for the top hit
            result = self._add_related_concepts(result, seen_concepts, top_k)
            return result

        # Tier 2: FAISS Semantic Search
        query_emb = self.model.encode([query_text], convert_to_numpy=True)
        query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)

        semantic_results = []
        if self.index is not None:
            scores, indices = self.index.search(query_emb, top_k)
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.kb) and idx >= 0:
                    entry = self.kb[idx]
                    if entry["concept"] not in seen_concepts:
                        seen_concepts.add(entry["concept"])
                        semantic_results.append({
                            "concept": entry["concept"],
                            "score": float(score),
                            "match_tier": "semantic_faiss",
                            "kb_entry": entry
                        })
        else:
            # Fallback NumPy Cosine Similarity
            scores_arr = np.dot(self.embeddings, query_emb.T).squeeze(axis=1)
            top_indices = np.argsort(scores_arr)[::-1][:top_k]
            for idx in top_indices:
                entry = self.kb[idx]
                if entry["concept"] not in seen_concepts:
                    seen_concepts.add(entry["concept"])
                    semantic_results.append({
                        "concept": entry["concept"],
                        "score": float(scores_arr[idx]),
                        "match_tier": "semantic_faiss",
                        "kb_entry": entry
                    })

        # Combine, de-duplicate, preserve priority order
        combined = exact_matches + semantic_results
        unique_results = []
        final_seen = set()
        for item in combined:
            if item["concept"] not in final_seen:
                final_seen.add(item["concept"])
                unique_results.append(item)

        unique_results = unique_results[:top_k]

        # Cross-retrieve related concepts for the top hit
        unique_results = self._add_related_concepts(unique_results, final_seen, top_k)
        return unique_results

    def _add_related_concepts(self, results: list, seen: set, top_k: int) -> list:
        """
        For the top-scoring result, retrieve its related_concepts from the KB
        and add any that are not already in the result set.
        This improves recall for culturally linked concepts.
        """
        if not results:
            return results

        top_entry = results[0]["kb_entry"]
        related_names = top_entry.get("related_concepts", [])
        if not related_names:
            return results

        # Build a concept name -> entry map
        concept_map = {e["concept"]: e for e in self.kb}

        for related_name in related_names:
            if len(results) >= top_k:
                break
            if related_name in seen:
                continue
            related_entry = concept_map.get(related_name)
            if related_entry:
                seen.add(related_name)
                results.append({
                    "concept": related_name,
                    "score": 0.5,  # Related concept boost
                    "match_tier": "related_concept",
                    "kb_entry": related_entry
                })

        return results
