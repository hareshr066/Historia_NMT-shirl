# IKS Tamil Translation Research Platform — Documentation

## Overview

A research-grade platform for **culturally-aware Classical Tamil → English translation** using:
- **Hybrid retrieval** (lexical + morphological + FAISS semantic) over a verified IKS Knowledge Base
- **IndicTrans2** as the primary translation model
- **LoRA fine-tuning** with versioned, reproducible checkpoints
- **Comprehensive evaluation** (BLEU, ROUGE-L, METEOR, BERTScore + IKS Concept Coverage)

---

## Project Structure

```
IKS PROJECT/
├── backend/
│   ├── ai/
│   │   ├── retrieval/
│   │   │   ├── augment.py          # IKS context augmentation (with JSONL logging)
│   │   │   ├── detector.py         # Tamil concept token detector
│   │   │   ├── ranker.py           # Contextual meaning ranker
│   │   │   └── retriever.py        # 4-tier hybrid retriever (lexical+morpho+substring+FAISS)
│   │   ├── translation/
│   │   │   └── nllb.py             # Translation interface (supports NLLB & IndicTrans2)
│   │   └── explain/
│   │       └── explanation.py      # Explainability module
│   ├── api/
│   │   └── translate.py            # FastAPI translation endpoint
│   └── core/
│       ├── auth.py                 # JWT authentication
│       └── config.py               # Environment configuration
│
├── configs/
│   └── config.yaml                 # Central configuration file
│
├── datasets/
│   ├── compile_dataset.py          # Multi-source dataset compiler
│   ├── train.jsonl                 # 298 training records
│   ├── validation.jsonl            # 37 validation records
│   └── test.jsonl                  # 38 test records
│
├── evaluation/
│   ├── eval.py                     # Comparative evaluation (BLEU/ROUGE/METEOR/BERTScore)
│   └── generate_human_review.py   # Human annotation CSV generator
│
├── knowledge_base/
│   ├── compile_kb.py               # KB compiler (80+ verified IKS concepts)
│   ├── iks_kb.json                 # Full KB (JSON)
│   ├── iks_kb.csv                  # Full KB (CSV)
│   └── iks_kb.parquet              # Full KB (Parquet)
│
├── models/checkpoint/
│   └── best_lora_adapter/          # Active LoRA adapter
│
├── results/
│   ├── augmentation_log.jsonl      # Per-request augmentation decisions
│   ├── training_log.jsonl          # Per-training-run metrics
│   ├── evaluation_results.json     # Comparative metrics
│   ├── evaluation_results_records.jsonl  # Per-record predictions for human review
│   ├── human_review.csv            # Annotator spreadsheet
│   └── error_analysis.md          # Qualitative error analysis
│
├── scripts/
│   ├── model_registry.py           # Checkpoint manager (list + set-active)
│   ├── run_pipeline.py             # End-to-end pipeline orchestrator
│   └── ranker.py                   # Batch ranking utilities
│
└── training/
    └── finetune.py                 # LoRA fine-tuning with versioned checkpoints
```

---

## Data Pipeline

### Phase 1 — Dataset Compilation

```bash
python -X utf8 datasets/compile_dataset.py
```

**Sources (public domain):**
| Source | Type | Records |
|--------|------|---------|
| Thirukkural | Ethics | 1,330 couplets (compiled) |
| Purananuru | Heroic poetry | 400 poems |
| Kurunthogai | Love poetry | 401 poems |
| Natrinai | Akam poetry | 400 poems |
| Akananuru | Love poetry | 400 poems |
| Silappathikaram | Epic | ~30 cantos |
| Manimekalai | Buddhist epic | ~30 cantos |
| Pathitrupathu | Royal praise | 80 poems |

**Output:** `datasets/train.jsonl`, `validation.jsonl`, `test.jsonl` (80/10/10 split, deduplicated)

Each record contains:
```json
{
  "id": "thirukkural_001",
  "source_book": "Thirukkural",
  "verse": "1.01",
  "era": "Post-Sangam",
  "translator": "G.U. Pope",
  "tamil": "அகர முதல எழுத்தெல்லாம் ஆதி பகவன் முதற்றே உலகு",
  "english": "A, as its first of letters, every speech maintains; ...",
  "augmented_tamil": "[CONCEPT] IRAIVAN [MEANING] God [ERA] Post-Sangam ... அகர முதல...",
  "iks_concepts": ["Iraivan"],
  "license": "Public Domain",
  "notes": "Cultural context notes..."
}
```

---

### Phase 2 — Knowledge Base

```bash
python -X utf8 knowledge_base/compile_kb.py
```

**80 fully verified concepts** covering:
- Core philosophical values (Aram, Anbu, Arul, Oozh, Thavam, Inbam)
- Thirukkural chapter virtues (Ozhukkam, Vaimai, Kollamai, Igai, Karpu, etc.)
- 5 Tinai landscapes (Kurinji, Mullai, Marutham, Neythal, Palai)
- 7 Puram warfare genres (Vetchi, Karanthai, Vanji, Kanchi, Nochi, Uzhignai, Thumbai, Vakai)
- 8 Meyppadus / emotional states (Nakai, Alukai, Marutkai, Acham, Perumitham, Vekuli, Uvakai)
- Literary concepts (Uvamam, Ullurai, Yazh, Pan, Koothu, Nool, Venpa)
- Social roles (Thozhi, Panan, Virali, Vallal, Pulavan, Kanavan, Manaivi, Kelir)

Each entry has: `concept_id`, `tamil`, `romanization`, `era`, `historical_meaning`, `modern_meaning`, `commentary_reference`, `source_reference`, `related_concepts`, `example_sentence`, `example_translation`, `confidence`, `verified_by`.

---

## Retrieval Pipeline (Phase 3)

The **4-tier hybrid retriever** in `backend/ai/retrieval/retriever.py`:

1. **Lexical Exact** (score=2.0) — direct Tamil word match
2. **Morphological Root** (score=1.5) — 50+ suffix-stripping rules for Tamil agglutination
3. **Substring Prefix** (score=1.2) — 3-character prefix containment
4. **FAISS Semantic** (score=cosine) — sentence-transformer embedding search
5. **Related Concept Cross-Retrieval** (score=0.5) — follows `related_concepts` links

---

## Fine-Tuning (Phase 4)

```bash
python training/finetune.py
```

Uses LoRA/PEFT (via HuggingFace `peft`), configured in `configs/config.yaml`:
```yaml
training:
  lora:
    r: 16
    alpha: 32
    dropout: 0.1
    target_modules: [q_proj, v_proj]
  early_stopping_patience: 3
  warmup_ratio: 0.1
  bf16: true  # with fp16 fallback on older hardware
```

Each run creates a **timestamped checkpoint directory**:
```
models/checkpoint/20260626_105000_ai4bharat_indictrans2/
  ├── adapter_model/       # LoRA weights
  ├── tokenizer/           # Tokenizer
  ├── metrics.json         # Train loss, eval loss, runtime
  ├── training_args.json   # All hyperparameters
  ├── dataset_version.txt  # Hash of training data
  ├── kb_version.txt       # Hash of knowledge base
  └── config_snapshot.yaml # Config at time of training
```

---

## Model Registry (Phase 8)

```bash
# List all checkpoints with metrics
python scripts/model_registry.py list

# Set a specific checkpoint as active
python scripts/model_registry.py set-active 20260626_105000_ai4bharat_indictrans2
```

---

## Evaluation (Phases 6 & 7)

```bash
# Run full comparative evaluation
python evaluation/eval.py

# Generate human review CSV
python evaluation/generate_human_review.py
```

**Metrics reported:**
- **BLEU** (corpus-level via SacreBLEU)
- **ROUGE-L** (token F-measure)
- **METEOR** (morphological alignment)
- **BERTScore** (semantic similarity via bert-score)
- **IKS Concept Coverage %** (how often IKS concept names appear in fine-tuned output)
- **Per-source-book breakdown** (Thirukkural vs Purananuru vs Akananuru, etc.)

---

## Augmentation (Phase 5)

Every request to `augment_sentence()` logs to `results/augmentation_log.jsonl`:
```json
{
  "timestamp_utc": "2026-06-26T10:00:00",
  "input": "அறம் செய விரும்பு",
  "augmented": "[CONCEPT] ARAM [MEANING] Virtue [ERA] Post-Sangam ... அறம் செய விரும்பு",
  "augmentation_method": "morphological",
  "concepts_found": 1,
  "concepts": [{"concept": "Aram", "method": "morphological", "confidence": 85.2}],
  "latency_ms": 12.3
}
```

---

## Running the Full Pipeline

```bash
# Step 1: Compile dataset
python -X utf8 datasets/compile_dataset.py

# Step 2: Build knowledge base
python -X utf8 knowledge_base/compile_kb.py

# Step 3: Run fine-tuning
python training/finetune.py

# Step 4: Evaluate
python evaluation/eval.py

# Step 5: Generate human review CSV
python evaluation/generate_human_review.py

# Step 6: Start the backend server
uvicorn backend.main:app --reload

# Step 7: Start the Streamlit UI
streamlit run frontend/app.py
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| No synthetic `Concept_N` KB entries | Research correctness — all concepts are verified against classical sources |
| Timestamped checkpoints | Reproducibility — no run overwrites another |
| Augmentation JSONL log | Audit trail — every augmentation decision is traceable |
| 4-tier retrieval | Handles Tamil's agglutinative morphology where simple exact match fails |
| Related concept cross-retrieval | Improves recall for culturally interlinked concepts (e.g., Aram → Anbu → Arul) |
| Public domain sources only | Ethical data sourcing — no scraping of copyrighted works |
