class IKSExplainer:
    def __init__(self):
        pass

    def generate_explanation(self, original_text, translation, augmentation_details):
        """
        Formats a detailed explainable report justifying the selected meaning and translation.
        """
        report = []
        report.append("==================================================")
        report.append("EXPLAINABLE NMT OUTPUT")
        report.append("==================================================")
        report.append(f"Input Text:         {original_text}")
        report.append(f"English Translation: {translation}")
        report.append("--------------------------------------------------")
        
        if not augmentation_details:
            report.append("No specialized IKS concepts detected in the source text.")
            report.append("Standard baseline NMT translation was applied.")
        else:
            report.append("IKS Context Injection details:")
            for idx, det in enumerate(augmentation_details, 1):
                report.append(f"\nConcept #{idx}: {det['tamil']} ({det['concept']})")
                
                # Candidates list
                cands_str = ", ".join(det["candidates"])
                report.append(f"  - Meaning Candidates: {cands_str}")
                
                # Selected meaning
                report.append(f"  - Selected Meaning:   {det['selected_meaning']}")
                report.append(f"  - Confidence:         {det['confidence']}%")
                report.append(f"  - Injected Tag:       [{det['concept'].upper()}={det['tag_value']}]")
                
                # Reason
                report.append(f"  - Justification:      {det['reason']}")
                
        report.append("==================================================")
        return "\n".join(report)

if __name__ == "__main__":
    # Test
    explainer = IKSExplainer()
    dummy_details = [{
        "concept": "Aram",
        "tamil": "அறம்",
        "selected_meaning": "Virtue, moral duty, righteousness",
        "tag_value": "VIRTUE",
        "confidence": 94.0,
        "candidates": ["Virtue, moral duty, righteousness", "Domestic life", "Ascetic life"],
        "reason": "Selected because Sangam context best matches Virtue."
    }]
    output = explainer.generate_explanation("அறம் செய விரும்பு", "Desire to practice virtue", dummy_details)
    print(output)
