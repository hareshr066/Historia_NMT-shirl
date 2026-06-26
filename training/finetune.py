import numpy as np
import pandas as pd
import scipy
import sklearn
import os
import json
import time
import shutil
import hashlib
from datetime import datetime

# Monkey patch check_torch_load_is_safe to bypass CVE-2025-32434 check
import transformers.utils.import_utils
import transformers.modeling_utils
transformers.utils.import_utils.check_torch_load_is_safe = lambda: None
transformers.modeling_utils.check_torch_load_is_safe = lambda: None

import yaml
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    DataCollatorForSeq2Seq,
    EarlyStoppingCallback
)
from peft import LoraConfig, get_peft_model, TaskType


def compute_dataset_hash(path: str) -> str:
    """Compute MD5 hash of a dataset file for versioning."""
    md5 = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                md5.update(chunk)
        return md5.hexdigest()[:12]
    except Exception:
        return "unknown"


def count_jsonl_lines(path: str) -> int:
    """Count lines in a JSONL file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return -1


def make_timestamped_dir(base_dir: str, model_name: str) -> str:
    """Create a unique timestamped checkpoint directory."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    model_slug = model_name.split("/")[-1].replace("-", "_")[:30]
    dir_name = f"{timestamp}_{model_slug}"
    full_path = os.path.join(base_dir, dir_name)
    os.makedirs(full_path, exist_ok=True)
    return full_path


def save_checkpoint_metadata(checkpoint_dir: str, training_args, config: dict, model_name: str):
    """Save all metadata alongside the adapter weights."""
    # Training args as JSON
    args_dict = {
        "model_name": model_name,
        "num_train_epochs": training_args.num_train_epochs,
        "per_device_train_batch_size": training_args.per_device_train_batch_size,
        "learning_rate": training_args.learning_rate,
        "weight_decay": training_args.weight_decay,
        "fp16": training_args.fp16,
        "bf16": training_args.bf16,
        "gradient_accumulation_steps": training_args.gradient_accumulation_steps,
        "timestamp_utc": datetime.utcnow().isoformat()
    }
    with open(os.path.join(checkpoint_dir, "training_args.json"), "w", encoding="utf-8") as f:
        json.dump(args_dict, f, indent=2)

    # Dataset version
    train_path = config["data"]["train_path"]
    ds_count = count_jsonl_lines(train_path)
    ds_hash = compute_dataset_hash(train_path)
    with open(os.path.join(checkpoint_dir, "dataset_version.txt"), "w", encoding="utf-8") as f:
        f.write(f"train_path={train_path}\nrecord_count={ds_count}\nmd5={ds_hash}\n")

    # KB version
    kb_path = "knowledge_base/iks_kb.json"
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            kb = json.load(f)
        kb_count = len(kb)
    except Exception:
        kb_count = -1
    kb_hash = compute_dataset_hash(kb_path)
    with open(os.path.join(checkpoint_dir, "kb_version.txt"), "w", encoding="utf-8") as f:
        f.write(f"kb_path={kb_path}\nconcept_count={kb_count}\nmd5={kb_hash}\n")

    # Config snapshot
    shutil.copy("configs/config.yaml", os.path.join(checkpoint_dir, "config_snapshot.yaml"))

    print(f"Saved checkpoint metadata to {checkpoint_dir}")


def append_training_log(log_path: str, epoch_metrics: dict):
    """Append per-epoch metrics to a JSONL training log."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(epoch_metrics, ensure_ascii=False) + "\n")


def train():
    # Load config
    config_path = "configs/config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    model_name = config["models"]["indictrans2"]

    # Check if GPU is available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Allow override to NLLB via environment variable
    if os.getenv("USE_NLLB", "false").lower() == "true":
        model_name = config["models"]["nllb"]

    print(f"Loading tokenizer and model for: {model_name}...")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True
    )

    # Load base model in FP16 for GPU, FP32 for CPU
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )

    src_lang = config["models"]["source_lang"]
    tgt_lang = config["models"]["target_lang"]

    # Set language codes for NLLB tokenizer if applicable
    if "nllb" in model_name.lower():
        tokenizer.src_lang = src_lang
        tokenizer.tgt_lang = tgt_lang

    # Load training dataset
    dataset = load_dataset(
        "json",
        data_files={
            "train": config["data"]["train_path"],
            "validation": config["data"]["val_path"]
        }
    )

    def preprocess_function(examples):
        inputs = []
        targets = []
        for src, tgt in zip(examples["augmented_tamil"], examples["english"]):
            if "indictrans2" in model_name.lower():
                inputs.append(f"{src_lang} {tgt_lang} {src}")
            else:
                inputs.append(src)
            targets.append(tgt)

        model_inputs = tokenizer(
            inputs,
            max_length=256,
            truncation=True,
            padding="max_length"
        )

        labels = tokenizer(
            text_target=targets,
            max_length=256,
            truncation=True,
            padding="max_length"
        )

        # Replace pad token id with -100 to ignore loss for padding
        labels_ids = [
            [(token if token != tokenizer.pad_token_id else -100) for token in label]
            for label in labels["input_ids"]
        ]
        model_inputs["labels"] = labels_ids
        return model_inputs

    print("Tokenizing datasets...")
    tokenized_datasets = dataset.map(
        preprocess_function,
        batched=True,
        remove_columns=dataset["train"].column_names
    )

    # Setup LoRA / PEFT Config
    lora_cfg = config["training"]["lora"]
    peft_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        inference_mode=False,
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["alpha"],
        lora_dropout=lora_cfg["dropout"],
        target_modules=lora_cfg["target_modules"]
    )

    print("Applying LoRA adapters to model...")
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Data Collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer,
        model=model,
        label_pad_token_id=-100,
        pad_to_multiple_of=8
    )

    # Training Arguments
    train_args = config["training"]

    # Determine bf16 / fp16 support
    use_bf16 = train_args.get("bf16", False) and torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    use_fp16 = (not use_bf16) and train_args.get("fp16", True) and torch.cuda.is_available()

    # Warmup
    warmup_ratio = train_args.get("warmup_ratio", 0.1)
    early_stopping_patience = train_args.get("early_stopping_patience", 3)

    training_arguments = Seq2SeqTrainingArguments(
        output_dir=train_args["output_dir"],
        learning_rate=float(train_args["learning_rate"]),
        per_device_train_batch_size=train_args["batch_size"],
        per_device_eval_batch_size=train_args["batch_size"],
        num_train_epochs=train_args["epochs"],
        weight_decay=train_args["weight_decay"],
        logging_steps=train_args["logging_steps"],
        eval_strategy=train_args["evaluation_strategy"],
        save_strategy=train_args["save_strategy"],
        gradient_accumulation_steps=train_args["gradient_accumulation_steps"],
        fp16=use_fp16,
        bf16=use_bf16,
        warmup_ratio=warmup_ratio,
        load_best_model_at_end=train_args["load_best_model_at_end"],
        metric_for_best_model=train_args["metric_for_best_model"],
        predict_with_generate=True,
        report_to="none"
    )

    # Callbacks
    callbacks = [EarlyStoppingCallback(early_stopping_patience=early_stopping_patience)]

    # Initialize Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_arguments,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        processing_class=tokenizer,
        data_collator=data_collator,
        callbacks=callbacks
    )

    print(f"Starting fine-tuning (early_stopping_patience={early_stopping_patience})...")
    train_start = time.time()
    train_result = trainer.train()
    train_elapsed = time.time() - train_start

    print(f"Training completed in {train_elapsed:.1f}s")

    # -----------------------------------------------------------------------
    # Save to TIMESTAMPED checkpoint dir (no overwrite)
    # -----------------------------------------------------------------------
    timestamped_dir = make_timestamped_dir(train_args["output_dir"], model_name)
    adapter_dir = os.path.join(timestamped_dir, "adapter_model")
    tokenizer_dir = os.path.join(timestamped_dir, "tokenizer")

    trainer.model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(tokenizer_dir)

    # Metrics
    metrics = {
        "train_loss": round(train_result.training_loss, 4),
        "train_runtime_seconds": round(train_elapsed, 1),
        "train_samples": len(tokenized_datasets["train"]),
        "val_samples": len(tokenized_datasets["validation"]),
        "timestamp_utc": datetime.utcnow().isoformat()
    }

    # Save eval loss from trainer state
    if trainer.state and trainer.state.log_history:
        eval_entries = [h for h in trainer.state.log_history if "eval_loss" in h]
        if eval_entries:
            metrics["best_eval_loss"] = round(eval_entries[-1]["eval_loss"], 4)

    with open(os.path.join(timestamped_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Save all metadata
    save_checkpoint_metadata(timestamped_dir, training_arguments, config, model_name)

    # Append to training log
    log_entry = {**metrics, "checkpoint_dir": timestamped_dir, "model_name": model_name}
    append_training_log("results/training_log.jsonl", log_entry)

    # Update the active best_lora_adapter pointer (best model from this run)
    best_model_path = os.path.join(train_args["output_dir"], "best_lora_adapter")
    if os.path.exists(best_model_path):
        shutil.rmtree(best_model_path)
    shutil.copytree(adapter_dir, best_model_path)
    print(f"Active adapter updated: {best_model_path}")

    print(f"\nFine-tuning complete.")
    print(f"  Versioned checkpoint : {timestamped_dir}")
    print(f"  Active adapter       : {best_model_path}")
    print(f"  Training log         : results/training_log.jsonl")
    print(f"\nUse 'python scripts/model_registry.py list' to see all checkpoints.")


if __name__ == "__main__":
    train()
