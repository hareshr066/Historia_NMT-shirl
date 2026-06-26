import yaml
from detector import IKSConceptDetector
from retriever import IKSMeaningRetriever
from ranker import IKSMeaningRanker

class IKSInputAugmenter:
    def __init__(self, config_path="configs/config.yaml"):
        # Initialize sub-modules
        self.detector = IKSConceptDetector(config_path)
        self.retriever = IKSMeaningRetriever(config_path)
        self.ranker = IKSMeaningRanker(config_path)
        
        # Load index
        self.retriever.load_index()

    def augment_sentence(self, sentence):
        """
        Augments a Classical Tamil sentence by prepending the resolved IKS concepts.
        Example:
            Input: "அறம் செய விரும்பு"
            Output: "[ARAM=VIRTUE] அறம் செய விரும்பு"
        Returns:
            dict containing:
                - original: original sentence
                - augmented: augmented sentence
                - details: list of resolved concepts and their details
        """
        # 1. Detect concepts
        detected = self.detector.detect_iks_concepts(sentence)
        if not detected:
            return {
                "original": sentence,
                "augmented": sentence,
                "details": []
            }
            
        resolved_concepts = []
        tags = []
        
        # 2. For each detected concept, retrieve and rank meanings
        for item in detected:
            concept_name = item["concept"]
            tamil_word = item["tamil"]
            
            # Retrieve candidates (we query the retriever with the concept name or word)
            candidates = self.retriever.retrieve_candidates(tamil_word, top_k=3)
            
            # Rank the candidates using the sentence as context
            ranking_result = self.ranker.rank_meanings(sentence, candidates)
            
            if ranking_result:
                best_meaning = ranking_result["english_meaning"]
                # Clean up meaning to be a concise tag value (take first part before semicolon/comma)
                clean_meaning = best_meaning.split(",")[0].split(";")[0].split("/")[0].strip().upper()
                
                # Format tag prefix
                tag = f"[{concept_name.upper()}={clean_meaning}]"
                tags.append(tag)
                
                resolved_concepts.append({
                    "concept": concept_name,
                    "tamil": tamil_word,
                    "selected_meaning": best_meaning,
                    "tag_value": clean_meaning,
                    "confidence": ranking_result["confidence_percent"],
                    "similarity": ranking_result["similarity_score"],
                    "candidates": [c["kb_entry"]["english"] for c in ranking_result["ranked_candidates"]],
                    "reason": f"Selected because the sentence context matches the historical meaning of {concept_name} as '{best_meaning}'."
                })
                
        # Prepend tags to original sentence
        prefix = "".join(tags)
        augmented_sentence = f"{prefix} {sentence}" if prefix else sentence
        
        return {
            "original": sentence,
            "augmented": augmented_sentence,
            "details": resolved_concepts
        }

if __name__ == "__main__":
    # Test augmentation
    augmenter = IKSInputAugmenter()
    
    samples = [
        "அறம் செய விரும்பு",
        "அன்பிலார் எல்லாம் தமக்குரியர் அன்புடையார் என்பும் உரியர் பிறர்க்கு.",
        "அருட்செல்வம் செல்வத்துள் செல்வம் பொருட்செல்வம் பூரியார் கண்ணும் உள."
    ]
    
    for s in samples:
        res = augmenter.augment_sentence(s)
        print(f"Original:  {res['original']}")
        print(f"Augmented: {res['augmented']}")
        print("Details:")
        for det in res["details"]:
            print(f"  - {det['concept']}: {det['selected_meaning']} (Conf: {det['confidence']}%)")
        print("-" * 50)
