"""
Human Review CSV Generator — Phase 7
=====================================
Loads test records + baseline + fine-tuned predictions and generates
a spreadsheet for human expert annotation.

Usage:
  python evaluation/generate_human_review.py
  python evaluation/generate_human_review.py --results results/evaluation_results.json
"""

import os
import json
import argparse
import csv
from pathlib import Path

import yaml

def load_jsonl(path: str) -> list:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def main():
    parser = argparse.ArgumentParser(description="Generate Human Review CSV")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--results", default="results/evaluation_results.json")
    parser.add_argument("--output", default="results/human_review.csv")
    args = parser.parse_args()

    # Load config
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    test_path = config["data"]["test_path"]

    # Load test records
    if not os.path.exists(test_path):
        print(f"ERROR: Test file not found at {test_path}. Run preprocess.py first.")
        return

    test_records = load_jsonl(test_path)
    print(f"Loaded {len(test_records)} test records.")

    # Load evaluation results (if they exist)
    baseline_preds = []
    finetuned_preds = []
    if os.path.exists(args.results):
        with open(args.results, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
        baseline_preds = eval_data.get("baseline_predictions", [])
        finetuned_preds = eval_data.get("finetuned_predictions", [])
        print(f"Loaded evaluation predictions from {args.results}")
    else:
        print(f"Warning: Evaluation results not found at {args.results}.")
        print("Generating CSV with empty prediction columns for manual filling.")

    # Pad prediction lists if needed
    while len(baseline_preds) < len(test_records):
        baseline_preds.append("")
    while len(finetuned_preds) < len(test_records):
        finetuned_preds.append("")

    # Generate CSV
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    columns = [
        "ID",
        "Source_Book",
        "Verse",
        "Era",
        "Translator",
        "Input_Tamil",
        "Reference_English",
        "Baseline_Translation",
        "FIneTuned_Translation",
        "IKS_Concepts",
        "Cultural_Notes",
        "Reviewer_Fluency_Score (1-5)",
        "Reviewer_Adequacy_Score (1-5)",
        "Reviewer_Concept_Accuracy_Score (1-5)",
        "Reviewer_Notes"
    ]

    rows = []
    for i, record in enumerate(test_records):
        concepts = record.get("iks_concepts", [])
        if isinstance(concepts, list):
            concepts_str = ", ".join(concepts)
        else:
            concepts_str = str(concepts)

        rows.append({
            "ID": record.get("id", f"R{i+1:04d}"),
            "Source_Book": record.get("source_book", ""),
            "Verse": record.get("verse", ""),
            "Era": record.get("era", ""),
            "Translator": record.get("translator", ""),
            "Input_Tamil": record.get("tamil", ""),
            "Reference_English": record.get("english", ""),
            "Baseline_Translation": baseline_preds[i],
            "FIneTuned_Translation": finetuned_preds[i],
            "IKS_Concepts": concepts_str,
            "Cultural_Notes": record.get("notes", ""),
            "Reviewer_Fluency_Score (1-5)": "",
            "Reviewer_Adequacy_Score (1-5)": "",
            "Reviewer_Concept_Accuracy_Score (1-5)": "",
            "Reviewer_Notes": ""
        })

    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nGenerated human review CSV: {args.output}")
    print(f"  Rows: {len(rows)}")
    print(f"  Columns: {len(columns)}")
    print(f"\nReviewers should fill in:")
    print(f"  Reviewer_Fluency_Score (1-5)   : How natural and fluent is the translation?")
    print(f"  Reviewer_Adequacy_Score (1-5)  : Does it preserve meaning?")
    print(f"  Reviewer_Concept_Accuracy (1-5): Is the IKS concept correctly conveyed?")
    print(f"  Reviewer_Notes                 : Any free-text observations.")

if __name__ == "__main__":
    main()
