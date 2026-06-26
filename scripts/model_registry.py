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
            meta.update(json.load(f))

    # Load training args
    args_path = checkpoint_dir / "training_args.json"
    if args_path.exists():
        with open(args_path, "r", encoding="utf-8") as f:
            args = json.load(f)
            meta["model"] = args.get("model_name", "unknown")
            meta["epochs"] = args.get("num_train_epochs", "?")
            meta["batch_size"] = args.get("per_device_train_batch_size", "?")
            meta["learning_rate"] = args.get("learning_rate", "?")

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

    # Determine active
    active_name = None
    if ACTIVE_LINK.exists() and ACTIVE_LINK.is_dir():
        try:
            active_name = ACTIVE_LINK.resolve().name
        except Exception:
            active_name = None

    print(f"\n{'='*90}")
    print(f"{'CHECKPOINT':<35} {'ACTIVE':<8} {'MODEL':<30} {'BLEU':>6} {'ROUGE-L':>8} {'DATASET':>12}")
    print(f"{'-'*90}")

    for ckpt in checkpoints:
        meta = _load_meta(ckpt)
        is_active = "YES <--" if ckpt.name == active_name else ""
        bleu = meta.get("bleu", "-")
        rougeL = meta.get("rougeL", "-")
        model = meta.get("model", "unknown")[:28]
        ds_ver = meta.get("dataset_version", "?")[:10]
        print(f"{ckpt.name:<35} {is_active:<8} {model:<30} {str(bleu):>6} {str(rougeL):>8} {ds_ver:>12}")

    print(f"{'='*90}")
    print(f"Total: {len(checkpoints)} checkpoint(s)")
    if active_name:
        print(f"Active: {active_name}")
    else:
        print("No active checkpoint set. Use: python scripts/model_registry.py set-active <dir>")

def cmd_set_active(checkpoint_name: str):
    """Set a checkpoint as the active best_lora_adapter."""
    target = MODELS_DIR / checkpoint_name

    if not target.exists():
        print(f"ERROR: Checkpoint '{checkpoint_name}' does not exist at {MODELS_DIR}")
        available = [d.name for d in MODELS_DIR.iterdir() if d.is_dir() and d.name != "best_lora_adapter"]
        print(f"Available checkpoints: {available}")
        sys.exit(1)

    # On Windows we copy instead of symlink (symlinks require admin)
    if ACTIVE_LINK.exists():
        if ACTIVE_LINK.is_dir():
            shutil.rmtree(ACTIVE_LINK)
        else:
            ACTIVE_LINK.unlink()

    try:
        ACTIVE_LINK.symlink_to(target.resolve(), target_is_directory=True)
        print(f"Symlink created: {ACTIVE_LINK} -> {target}")
    except OSError:
        # Fallback: copy (for Windows without symlink privileges)
        shutil.copytree(target, ACTIVE_LINK)
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
