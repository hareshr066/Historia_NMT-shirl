import os
import re
import json
from backend.core.config import KB_JSON_PATH

class IKSConceptDetector:
    def __init__(self):
        # Load Knowledge Base
        self.kb_path = KB_JSON_PATH
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.kb = json.load(f)
        else:
            self.kb = []
            
        # Create a lookup mapping from Tamil representation to concept entries
        self.tamil_to_concept = {}
        for entry in self.kb:
            self.tamil_to_concept[entry["tamil"].strip()] = entry

    def detect_iks_concepts(self, text: str) -> list:
        """
        Detects IKS concepts in the text using root matching.
        """
        detected = []
        if not text or not self.kb:
            return detected
            
        # Standardize text whitespace
        normalized_text = " ".join(text.split())
        
        for tamil_word, entry in self.tamil_to_concept.items():
            # Since Tamil is agglutinative, check if the root concept word is contained in the text.
            pattern = re.escape(tamil_word)
            matches = list(re.finditer(pattern, normalized_text))
            
            if matches:
                detected.append({
                    "concept": entry["concept"],
                    "tamil": entry["tamil"],
                    "english": entry["english"],
                    "confidence": 1.0,
                    "kb_entry": entry
                })
                
        # Remove duplicates and return unique list
        seen_concepts = set()
        unique_detected = []
        for item in detected:
            if item["concept"] not in seen_concepts:
                seen_concepts.add(item["concept"])
                unique_detected.append(item)
                
        return unique_detected
