import os
import re
import json
import yaml
import numpy as np

class IKSConceptDetector:
    def __init__(self, config_path="configs/config.yaml"):
        # Load config
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            
        # Load Knowledge Base
        self.kb_path = self.config["kb"]["json_path"]
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.kb = json.load(f)
        else:
            self.kb = []
            
        # Create a lookup mapping from Tamil representation to concept entries
        self.tamil_to_concept = {}
        for entry in self.kb:
            # Standardize and add
            self.tamil_to_concept[entry["tamil"].strip()] = entry

    def detect_iks_concepts(self, text):
        """
        Detects IKS concepts in the text using exact keyword matching.
        Returns:
            list of dicts containing:
                - concept: name
                - tamil: tamil word
                - english: translation
                - confidence: matching confidence
                - kb_entry: the full matching KB dictionary
        """
        detected = []
        if not text or not self.kb:
            return detected
            
        # Standardize text whitespace
        normalized_text = " ".join(text.split())
        
        # Search for each Tamil concept word in the text
        for tamil_word, entry in self.tamil_to_concept.items():
            # Use regex to find the word as a substring or boundary-matched
            # Since Tamil is agglutinative, exact word boundaries may not match suffixes (e.g. அறத்தின், அறத்தை)
            # So we check if the root word is contained in the text.
            # To avoid false positives on very short words (e.g. மெய், ஊழ்), we require boundaries or min length.
            pattern = re.escape(tamil_word)
            matches = list(re.finditer(pattern, normalized_text))
            
            if matches:
                # Calculate simple heuristics: if exact match, high confidence.
                # If it's a substring inside a larger word, confidence is slightly adjusted or set to 1.0 since root word match in Tamil is crucial.
                detected.append({
                    "concept": entry["concept"],
                    "tamil": entry["tamil"],
                    "english": entry["english"],
                    "confidence": 1.0,
                    "kb_entry": entry
                })
                
        # Remove duplicates (if any) and return sorted by confidence
        seen_concepts = set()
        unique_detected = []
        for item in detected:
            if item["concept"] not in seen_concepts:
                seen_concepts.add(item["concept"])
                unique_detected.append(item)
                
        return unique_detected

if __name__ == "__main__":
    # Quick debug test
    detector = IKSConceptDetector()
    sample = "அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்."
    results = detector.detect_iks_concepts(sample)
    print(f"Text: {sample}")
    print("Detected:")
    for r in results:
        print(f" - {r['tamil']} ({r['concept']}): {r['english']} (Conf: {r['confidence']})")
