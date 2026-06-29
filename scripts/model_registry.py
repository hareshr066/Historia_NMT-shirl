"""
Model Version Registry
======================
Lists all checkpoint directories, shows metrics, and marks one as active.
Usage:
  python scripts/model_registry.py list
  python scripts/model_registry.py set-active <checkpoint_dir_name>
"""

import os
import sys
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime

MODELS_DIR = Path("models/checkpoint")
ACTIVE_LINK = MODELS_DIR / "best_lora_adapter"

def _load_meta(checkpoint_dir: Path) -> dict:
    """Load metrics.json and training_args.json from a checkpoint directory."""
    meta = {"dir": checkpoint_dir.name, "timestamp": "unknown", "model": "unknown"}

    # Load metrics
    metrics_path = checkpoint_dir / "metrics.json"
    if metrics_path.exists():
        with open(metrics_path, "r", encoding="utf-8") as f:
            try:
                meta.update(json.load(f))
            except Exception:
                pass

    # Load training args
    args_path = checkpoint_dir / "training_args.json"
    if args_path.exists():
        with open(args_path, "r", encoding="utf-8") as f:
            try:
                args = json.load(f)
                meta["model"] = args.get("model_name", "unknown")
                meta["epochs"] = args.get("num_train_epochs", "?")
                meta["batch_size"] = args.get("per_device_train_batch_size", "?")
                meta["learning_rate"] = args.get("learning_rate", "?")
            except Exception:
                pass

    # Load dataset version
    ds_path = checkpoint_dir / "dataset_version.txt"
    if ds_path.exists():
        meta["dataset_version"] = ds_path.read_text().strip()

    # Load KB version
    kb_path = checkpoint_dir / "kb_version.txt"
    if kb_path.exists():
        meta["kb_version"] = kb_path.read_text().strip()

    return meta

def cmd_list():
    """List all checkpoints with their metrics."""
    # Import active translation model configuration
    try:
        from backend.core.config import (
            TRANSLATION_MODEL_NAME, 
            TRANSLATION_MODEL_TYPE, 
            LORA_ADAPTER_PATH
        )
    except ImportError:
        TRANSLATION_MODEL_NAME = "ai4bharat/indictrans2-indic-en-dist-200M"
        TRANSLATION_MODEL_TYPE = "indictrans2"
        LORA_ADAPTER_PATH = "models/checkpoint/best_lora_adapter"

    # Determine Active LoRA Adapter and version info
    lora_active_path = "None"
    model_version = "v1.0-default"
    training_dataset_version = "IKS-Parallel-v1.0"
    evaluation_version = "IN22-Gen / Classical-Tamil-Eval-v1"

    if os.path.exists(LORA_ADAPTER_PATH):
        lora_active_path = os.path.abspath(LORA_ADAPTER_PATH)
        
        # Load version tags from files if they exist
        for fname, var_name in [
            ("model_version.txt", "model_version"),
            ("dataset_version.txt", "training_dataset_version"),
            ("evaluation_version.txt", "evaluation_version")
        ]:
            fpath = os.path.join(LORA_ADAPTER_PATH, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        if var_name == "model_version":
                            model_version = content
                        elif var_name == "training_dataset_version":
                            training_dataset_version = content
                        elif var_name == "evaluation_version":
                            evaluation_version = content

    print("\n" + "="*95)
    print("                       CHRONOIKS MODEL REGISTRY STATUS")
    print("="*95)
    print(f"Active Translation Model : {TRANSLATION_MODEL_NAME} ({TRANSLATION_MODEL_TYPE})")
    print(f"Active LoRA Adapter      : {lora_active_path}")
    print(f"Model Version            : {model_version}")
    print(f"Training Dataset Version : {training_dataset_version}")
    print(f"Evaluation Version       : {evaluation_version}")
    print("="*95)

    if not MODELS_DIR.exists():
        print(f"No checkpoints found at {MODELS_DIR}. Run finetune.py first.")
        return

    checkpoints = sorted(
        [d for d in MODELS_DIR.iterdir() if d.is_dir() and d.name != "best_lora_adapter"],
        key=lambda d: d.stat().st_mtime, reverse=True
    )

    if not checkpoints:
        print("No checkpoint directories found.")
        return

    # Determine active checkpoint folder
    active_name = None
    if ACTIVE_LINK.exists() and ACTIVE_LINK.is_dir():
        try:
            # Resolve symlink or check directory contents
            if ACTIVE_LINK.is_symlink():
                active_name = os.readlink(ACTIVE_LINK).split(os.sep)[-1]
            else:
                # If copy, we look for a unique metadata file or the checkpoint directory name
                meta_file = ACTIVE_LINK / "checkpoint_source.txt"
                if meta_file.exists():
                    active_name = meta_file.read_text().strip()
        except Exception:
            active_name = None

    print(f"{'CHECKPOINT':<35} {'ACTIVE':<8} {'BASE MODEL':<30} {'BLEU':>6} {'ROUGE-L':>8} {'DATASET':>12}")
    print(f"{'-'*95}")

    for ckpt in checkpoints:
        meta = _load_meta(ckpt)
        is_active = "YES <--" if ckpt.name == active_name else ""
        bleu = meta.get("bleu", "-")
        rougeL = meta.get("rougeL", "-")
        model = meta.get("model", "unknown")[:28]
        ds_ver = meta.get("dataset_version", "?")[:10]
        print(f"{ckpt.name:<35} {is_active:<8} {model:<30} {str(bleu):>6} {str(rougeL):>8} {ds_ver:>12}")

    print(f"{'='*95}")
    print(f"Total: {len(checkpoints)} checkpoint(s)")
    if active_name:
        print(f"Active Checkpoint Folder: {active_name}")
    else:
        print("No active checkpoint directory set. Use: python scripts/model_registry.py set-active <dir>")

def cmd_set_active(checkpoint_name: str):
    """Set a checkpoint as the active best_lora_adapter."""
    target = MODELS_DIR / checkpoint_name

    if not target.exists():
        print(f"ERROR: Checkpoint '{checkpoint_name}' does not exist at {MODELS_DIR}")
        available = [d.name for d in MODELS_DIR.iterdir() if d.is_dir() and d.name != "best_lora_adapter"]
        print(f"Available checkpoints: {available}")
        sys.exit(1)

    # Clean up previous ACTIVE_LINK
    if ACTIVE_LINK.exists():
        if ACTIVE_LINK.is_dir() and not ACTIVE_LINK.is_symlink():
            shutil.rmtree(ACTIVE_LINK)
        else:
            ACTIVE_LINK.unlink()

    # Create link or fallback copy
    try:
        ACTIVE_LINK.symlink_to(target.resolve(), target_is_directory=True)
        print(f"Symlink created: {ACTIVE_LINK} -> {target}")
    except OSError:
        # Fallback: copy (for Windows without symlink privileges)
        shutil.copytree(target, ACTIVE_LINK)
        # Store source checkpoint name to identify active status later
        with open(ACTIVE_LINK / "checkpoint_source.txt", "w", encoding="utf-8") as f:
            f.write(checkpoint_name)
        print(f"Copied checkpoint to: {ACTIVE_LINK}")

    print(f"Active checkpoint set to: {checkpoint_name}")
    print("The translation server will use this adapter on next startup.")

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        cmd_list()
    elif sys.argv[1] == "set-active":
        if len(sys.argv) < 3:
            print("Usage: python scripts/model_registry.py set-active <checkpoint_dir_name>")
            sys.exit(1)
        cmd_set_active(sys.argv[2])
    else:
        print(f"Unknown command: {sys.argv[1]}")
        print("Commands: list, set-active <dir>")
        sys.exit(1)

if __name__ == "__main__":
    main()
