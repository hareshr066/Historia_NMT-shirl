import os
import sys
import subprocess
import argparse

def run_step(command, description):
    print("\n" + "="*80)
    print(f"RUNNING STEP: {description}")
    print(f"Command:      {command}")
    print("="*80)
    
    # Run the command with the virtual environment's python
    # We use sys.executable if running inside the venv, otherwise we use .venv\Scripts\python
    python_bin = os.path.join(".venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join(".venv", "bin", "python")
    
    # If python_bin doesn't exist, fall back to current interpreter
    if not os.path.exists(python_bin):
        python_bin = sys.executable
        
    full_cmd = f'"{python_bin}" -u {command}'
    
    process = subprocess.Popen(full_cmd, shell=True)
    process.wait()
    
    if process.returncode != 0:
        print(f"\nERROR: Step '{description}' failed with exit code {process.returncode}")
        sys.exit(process.returncode)
    else:
        print(f"\nSUCCESS: Step '{description}' completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="IKS-Aware NMT Pipeline Orchestrator")
    parser.add_argument("--use_nllb", action="store_true", help="Use NLLB-200 instead of IndicTrans2 (useful to avoid gated repo checks)")
    parser.add_argument("--skip_training", action="store_true", help="Skip the PEFT fine-tuning step (useful for dry runs)")
    args = parser.parse_args()
    
    # Set environment variables if using NLLB
    if args.use_nllb:
        os.environ["USE_NLLB"] = "true"
        print("Pipeline configured to use NLLB-200 distilled 600M model.")
    else:
        os.environ["USE_NLLB"] = "false"
        print("Pipeline configured to use AI4Bharat IndicTrans2 model.")
        
    # Step 1: Compile Knowledge Base
    run_step("knowledge_base/compile_kb.py", "Compiling 200 IKS Concepts Database")
    
    # Step 2: Compile Parallel Dataset
    run_step("datasets/compile_dataset.py", "Compiling Parallel Sentence Dataset")
    
    # Step 3: Run Preprocessing & Augmentation
    run_step("scripts/preprocess.py", "Preprocessing Text and Performing Input Tag Augmentation")
    
    # Step 4: Run PEFT Fine-tuning (unless skipped)
    if not args.skip_training:
        run_step("training/finetune.py", "Fine-tuning Translation Model (PEFT/LoRA)")
    else:
        print("\nSkipping training step as requested.")
        
    # Step 5: Run Evaluation and Compare Models
    run_step("evaluation/eval.py", "Evaluating Baseline vs Fine-Tuned Model")
    
    print("\n" + "="*80)
    print("ALL PIPELINE STEPS COMPLETED SUCCESSFULLY!")
    print("="*80)

if __name__ == "__main__":
    main()
