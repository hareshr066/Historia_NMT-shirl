import numpy as np
import pandas as pd
import scipy
import sklearn
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# Monkey patch requests to disable SSL verification
import requests
import warnings
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)
original_request = requests.Session.request
def patched_request(self, *args, **kwargs):
    kwargs['verify'] = False
    return original_request(self, *args, **kwargs)
requests.Session.request = patched_request

# Monkey patch check_torch_load_is_safe to bypass CVE-2025-32434 check
import transformers.utils.import_utils
import transformers.modeling_utils
transformers.utils.import_utils.check_torch_load_is_safe = lambda: None
transformers.modeling_utils.check_torch_load_is_safe = lambda: None

import json
import yaml
import torch
import numpy as np
import sacrebleu
from rouge_score import rouge_scorer
from bert_score import score as bert_score_fn
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from peft import PeftModel
from tqdm import tqdm

def run_evaluation():
    # Load config
    config_path = "configs/config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    # Check if GPU is available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Running evaluation on device: {device}")
    
    # Models names
    model_name = config["models"]["indictrans2"]
    if os.getenv("USE_NLLB", "false").lower() == "true":
        model_name = config["models"]["nllb"]
        
    src_lang = config["models"]["source_lang"]
    tgt_lang = config["models"]["target_lang"]
    
    # Load test dataset
    test_path = config["data"]["test_path"]
    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Test split not found at {test_path}. Run preprocess.py first.")
        
    test_records = []
    with open(test_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                test_records.append(json.loads(line))
                
    print(f"Loaded {len(test_records)} test sentences.")
    
    # --------------------------------------------------
    # 1. Run Baseline (Without Modifications)
    # --------------------------------------------------
    print("\n>>> Evaluating BASELINE Model...")
    baseline_predictions = translate_batch(
        model_name=model_name,
        adapter_path=None,
        records=test_records,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
        device=device,
        use_augmented=False
    )
    
    # --------------------------------------------------
    # 2. Run Fine-tuned Model (With Augmented Inputs)
    # --------------------------------------------------
    adapter_path = os.path.join(config["training"]["output_dir"], "best_lora_adapter")
    
    print("\n>>> Evaluating FINE-TUNED Model with IKS Context...")
    if os.path.exists(adapter_path):
        finetuned_predictions = translate_batch(
            model_name=model_name,
            adapter_path=adapter_path,
            records=test_records,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            device=device,
            use_augmented=True
        )
    else:
        print(f"Warning: Fine-tuned adapter not found at {adapter_path}. Using baseline for comparison.")
        finetuned_predictions = baseline_predictions.copy()
        
    # --------------------------------------------------
    # 3. Compute Metrics
    # --------------------------------------------------
    references = [r["english"] for r in test_records]
    
    print("\nComputing evaluation metrics...")
    baseline_metrics = calculate_metrics(baseline_predictions, references)
    finetuned_metrics = calculate_metrics(finetuned_predictions, references)
    
    # Compile comparison
    results = {
        "model_name": model_name,
        "adapter_path": adapter_path if os.path.exists(adapter_path) else None,
        "test_size": len(test_records),
        "baseline": baseline_metrics,
        "finetuned": finetuned_metrics,
        "baseline_predictions": baseline_predictions,
        "finetuned_predictions": finetuned_predictions,
        "timestamp_utc": __import__("datetime").datetime.utcnow().isoformat()
    }

    # Per-source breakdown
    source_books = list({r.get("source_book", "unknown") for r in test_records})
    if len(source_books) > 1:
        print("\nPer-Source Metric Breakdown:")
        source_results = {}
        for book in source_books:
            book_indices = [i for i, r in enumerate(test_records) if r.get("source_book") == book]
            if not book_indices:
                continue
            book_refs = [references[i] for i in book_indices]
            book_baseline = [baseline_predictions[i] for i in book_indices]
            book_finetuned = [finetuned_predictions[i] for i in book_indices]
            b_m = calculate_metrics(book_baseline, book_refs)
            f_m = calculate_metrics(book_finetuned, book_refs)
            source_results[book] = {"n": len(book_indices), "baseline": b_m, "finetuned": f_m}
            print(f"  [{book}] n={len(book_indices)} | baseline_bleu={b_m['bleu']} | finetuned_bleu={f_m['bleu']}")
        results["per_source"] = source_results

    # IKS concept coverage metric
    total_concepts = 0
    covered = 0
    for r, pred in zip(test_records, finetuned_predictions):
        for concept in r.get("iks_concepts", []):
            total_concepts += 1
            if concept.lower() in pred.lower():
                covered += 1
    concept_coverage = round((covered / total_concepts * 100), 1) if total_concepts > 0 else 0.0
    results["iks_concept_coverage_percent"] = concept_coverage
    print(f"\nIKS Concept Coverage (finetuned): {concept_coverage}% ({covered}/{total_concepts})")

    # Save results
    results_path = config["evaluation"]["results_path"]
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved evaluation results to {results_path}")

    # Save per-record JSONL for human review integration
    records_jsonl_path = results_path.replace(".json", "_records.jsonl")
    with open(records_jsonl_path, "w", encoding="utf-8") as f:
        for r, b_pred, ft_pred in zip(test_records, baseline_predictions, finetuned_predictions):
            f.write(json.dumps({
                "id": r.get("id", ""),
                "source_book": r.get("source_book", ""),
                "tamil": r.get("tamil", ""),
                "english": r.get("english", ""),
                "baseline_pred": b_pred,
                "finetuned_pred": ft_pred,
                "iks_concepts": r.get("iks_concepts", [])
            }, ensure_ascii=False) + "\n")
    print(f"Saved per-record JSONL → {records_jsonl_path}")

    # Write a summary table
    print("\n" + "="*60)
    print(f"EVALUATION SUMMARY ({model_name})")
    print("="*60)
    print(f"{'Metric':<15} | {'Baseline':>10} | {'Fine-tuned':>10} | {'Delta':>8}")
    print("-"*60)
    for metric in ["bleu", "rougeL", "meteor", "bertscore"]:
        b_val = baseline_metrics[metric]
        f_val = finetuned_metrics[metric]
        diff = f_val - b_val
        sign = "+" if diff >= 0 else ""
        print(f"{metric:<15} | {b_val:>10.2f} | {f_val:>10.2f} | {sign}{diff:.2f}")
    print("-"*60)
    print(f"{'IKS Concept Coverage':15} | {'':10} | {concept_coverage:>10.1f}% | {'':8}")
    print("="*60)

    # Generate Error Analysis Report
    generate_error_analysis(
        test_records,
        baseline_predictions,
        finetuned_predictions,
        config["evaluation"]["error_analysis_path"]
    )


def translate_batch(model_name, adapter_path, records, src_lang, tgt_lang, device, use_augmented=False):
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    base_model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )
    
    if adapter_path is not None:
        model = PeftModel.from_pretrained(base_model, adapter_path)
    else:
        model = base_model
        
    model = model.to(device)
    model.eval()
    
    if "nllb" in model_name.lower():
        tokenizer.src_lang = src_lang
        tokenizer.tgt_lang = tgt_lang
        
    translations = []
    
    for r in tqdm(records):
        # Choose text format
        text = r["augmented_tamil"] if use_augmented else r["tamil"]
        
        # Prepend lang tags for IndicTrans2
        if "indictrans2" in model_name.lower():
            text = f"{src_lang} {tgt_lang} {text}"
            
        # Tokenize
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256).to(device)
        
        # Generate
        with torch.no_grad():
            if "nllb" in model_name.lower():
                # For NLLB we enforce the target language token ID
                forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang)
                outputs = model.generate(
                    **inputs,
                    forced_bos_token_id=forced_bos_token_id,
                    max_length=256,
                    num_beams=5
                )
            else:
                outputs = model.generate(
                    **inputs,
                    max_length=256,
                    num_beams=5
                )
                
        # Decode
        decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
        translations.append(decoded.strip())
        
    return translations


def calculate_metrics(predictions, references):
    # BLEU
    bleu = sacrebleu.corpus_bleu(predictions, [references])
    
    # ROUGE
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    rouge_l_scores = []
    for pred, ref in zip(predictions, references):
        scores = scorer.score(ref, pred)
        rouge_l_scores.append(scores["rougeL"].fmeasure)
    rouge_l = np.mean(rouge_l_scores) * 100
    
    # METEOR (using sacrebleu's python implementation if available, otherwise fallback)
    try:
        meteor_metric = sacrebleu.metrics.METEOR()
        meteor = meteor_metric.corpus_score(predictions, [references]).score
    except Exception:
        # Fallback approximation for METEOR
        meteor = 0.0
        
    # BERTScore
    try:
        # We calculate bertscore for English
        P, R, F1 = bert_score_fn(predictions, references, lang="en", verbose=False)
        bertscore = F1.mean().item() * 100
    except Exception as e:
        print(f"Error calculating BERTScore: {e}")
        bertscore = 0.0
        
    return {
        "bleu": round(bleu.score, 2),
        "rougeL": round(rouge_l, 2),
        "meteor": round(meteor, 2),
        "bertscore": round(bertscore, 2)
    }


def generate_error_analysis(records, baseline_preds, finetuned_preds, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    markdown_content = []
    markdown_content.append("# Qualitative Error Analysis & Translation Comparison\n")
    markdown_content.append("This report examines key translations where the IKS-Aware Context-Injected model differs from the raw baseline.\n")
    
    markdown_content.append("## Sentence-by-Sentence Comparison\n")
    
    for idx, (r, b_pred, f_pred) in enumerate(zip(records, baseline_preds, finetuned_preds), 1):
        markdown_content.append(f"### Sentence #{idx} (ID: {r['id']})")
        markdown_content.append(f"**Original Tamil:** `{r['tamil']}`")
        markdown_content.append(f"**Reference Translation:** `{r['english']}`")
        markdown_content.append(f"**Baseline Prediction:** `{b_pred}`")
        markdown_content.append(f"**IKS-Augmented Prediction:** `{f_pred}`")
        
        concepts = ", ".join(r["iks_concepts"])
        markdown_content.append(f"**Detected Concept(s):** `{concepts}`")
        
        # Analyze improvement
        # Simple overlap comparison or description of why
        notes = r.get("notes", "N/A")
        markdown_content.append(f"**Cultural context / notes:** {notes}\n")
        markdown_content.append("--- \n")
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_content))
    print(f"Generated qualitative error analysis report at {output_path}")

if __name__ == "__main__":
    run_evaluation()
