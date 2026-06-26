import os
import json
import time
from datetime import datetime

from backend.ai.retrieval.detector import IKSConceptDetector
from backend.ai.retrieval.retriever import IKSMeaningRetriever
from backend.ai.retrieval.ranker import IKSMeaningRanker

# Path for augmentation log
AUGMENTATION_LOG_PATH = "results/augmentation_log.jsonl"


def _append_augmentation_log(entry: dict):
    """Append one augmentation decision to the JSONL log file."""
    try:
        os.makedirs(os.path.dirname(AUGMENTATION_LOG_PATH), exist_ok=True)
        with open(AUGMENTATION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        # Non-fatal — do not disrupt augmentation if logging fails
        print(f"[augment_log] Warning: could not write log entry: {e}")


class IKSInputAugmenter:
    def __init__(self, log_augmentations: bool = True):
        self.detector = IKSConceptDetector()
        self.retriever = IKSMeaningRetriever()
        self.ranker = IKSMeaningRanker()
        self.retriever.load_index()
        self.log_augmentations = log_augmentations

    def augment_sentence(self, sentence: str) -> dict:
        """
        Augments a Classical Tamil sentence by prepending resolved IKS context tags.

        Example:
            Input:  "அறம் செய விரும்பு"
            Output: "[CONCEPT] ARAM [MEANING] Virtue [ERA] Post-Sangam [SOURCE] ...  அறம் செய விரும்பு"

        Returns a dict with:
            original          : str  — untouched input sentence
            augmented         : str  — context-prepended output
            augmentation_method : str — how it was matched (lexical/morphological/semantic)
            details           : list — per-concept resolution details
        """
        t0 = time.time()

        # 1. Detect root concepts
        detected = self.detector.detect_iks_concepts(sentence)

        if not detected:
            result = {
                "original": sentence,
                "augmented": sentence,
                "augmentation_method": "none",
                "details": []
            }
            if self.log_augmentations:
                _append_augmentation_log({
                    "timestamp_utc": datetime.utcnow().isoformat(),
                    "input": sentence,
                    "augmentation_method": "none",
                    "concepts_found": 0,
                    "latency_ms": round((time.time() - t0) * 1000, 1)
                })
            return result

        resolved_concepts = []
        tags = []
        all_methods = []

        # 2. Retrieve candidates and contextually rank meanings
        for item in detected:
            concept_name = item["concept"]
            tamil_word = item["tamil"]

            candidates = self.retriever.retrieve_candidates(tamil_word, top_k=3)
            ranking_result = self.ranker.rank_meanings(sentence, candidates)

            if not ranking_result:
                continue

            best_cand = ranking_result["ranked_candidates"][0]
            kb_entry = best_cand["kb_entry"]
            best_meaning = kb_entry["english"]
            era = kb_entry.get("era", "Classical")
            source = kb_entry.get("source_reference", "General Commentary")
            confidence = ranking_result["confidence_percent"]

            # Determine augmentation method from match score
            if best_cand.get("score", 0) >= 2.0:
                method = "lexical_exact"
            elif best_cand.get("score", 0) >= 1.0:
                method = "morphological"
            else:
                method = "semantic_faiss"
            all_methods.append(method)

            # Clean meaning for a concise tag
            clean_meaning = best_meaning.split(",")[0].split(";")[0].split("/")[0].strip()

            # Include related concepts in tag if high confidence
            related_ctx = ""
            if confidence > 70.0 and kb_entry.get("related_concepts"):
                related = ", ".join(kb_entry["related_concepts"][:2])
                related_ctx = f" [RELATED] {related}"

            tag = (
                f"[CONCEPT] {concept_name.upper()} "
                f"[MEANING] {clean_meaning} "
                f"[ERA] {era} "
                f"[SOURCE] {source}"
                f"{related_ctx}"
            )
            tags.append(tag)

            resolved_concepts.append({
                "concept": concept_name,
                "tamil": tamil_word,
                "selected_meaning": best_meaning,
                "tag_value": clean_meaning,
                "confidence": confidence,
                "similarity": ranking_result["similarity_score"],
                "augmentation_method": method,
                "candidates": [c["kb_entry"]["english"] for c in ranking_result["ranked_candidates"]],
                "reason": (
                    f"Selected via {method}: sentence context matches '{concept_name}' "
                    f"as '{best_meaning}' with {confidence:.1f}% confidence."
                )
            })

        # 3. Prepend tags
        prefix = " ".join(tags)
        augmented_sentence = f"{prefix} {sentence}" if prefix else sentence

        # Validate: augmented must always contain the original sentence
        assert sentence in augmented_sentence, (
            f"Augmentation validation failed: original not found in augmented string.\n"
            f"Original: {sentence}\nAugmented: {augmented_sentence}"
        )

        dominant_method = max(set(all_methods), key=all_methods.count) if all_methods else "none"
        elapsed_ms = round((time.time() - t0) * 1000, 1)

        # 4. Log augmentation decision
        if self.log_augmentations:
            log_entry = {
                "timestamp_utc": datetime.utcnow().isoformat(),
                "input": sentence,
                "augmented": augmented_sentence,
                "augmentation_method": dominant_method,
                "concepts_found": len(resolved_concepts),
                "concepts": [
                    {
                        "concept": c["concept"],
                        "method": c["augmentation_method"],
                        "confidence": c["confidence"]
                    }
                    for c in resolved_concepts
                ],
                "latency_ms": elapsed_ms
            }
            _append_augmentation_log(log_entry)

        return {
            "original": sentence,
            "augmented": augmented_sentence,
            "augmentation_method": dominant_method,
            "details": resolved_concepts
        }
