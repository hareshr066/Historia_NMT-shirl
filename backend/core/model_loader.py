import os
import gc
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
from backend.core.config import NLL_MODEL_PATH, LORA_ADAPTER_PATH, TRANSLATION_MODEL_NAME

class ModelLoader:
    _models = {}
    _tokenizers = {}
    _devices = {}

    @classmethod
    def get_device(cls, model_type: str) -> str:
        if model_type not in cls._devices:
            cls._devices[model_type] = "cuda" if torch.cuda.is_available() else "cpu"
        return cls._devices[model_type]

    @classmethod
    def load_tokenizer(cls, model_type: str, model_name_or_path: str):
        key = f"{model_type}_tokenizer"
        if key not in cls._tokenizers:
            print(f"Loading {model_type} tokenizer from {model_name_or_path}...")
            cls._tokenizers[key] = AutoTokenizer.from_pretrained(
                model_name_or_path, 
                trust_remote_code=True,
                token=os.getenv("HF_TOKEN")
            )
        return cls._tokenizers[key]

    @classmethod
    def load_model(cls, model_type: str, model_name_or_path: str, load_lora: bool = True):
        model_key = f"{model_type}_model"
        if model_key not in cls._models:
            device = cls.get_device(model_type)
            print(f"Loading {model_type} base model from {model_name_or_path} on {device}...")
            
            # Disable safety checks/warnings for loading PyTorch weights
            try:
                import transformers.utils.import_utils
                import transformers.modeling_utils
                transformers.utils.import_utils.check_torch_load_is_safe = lambda: None
                transformers.modeling_utils.check_torch_load_is_safe = lambda: None
            except Exception:
                pass

            dtype = torch.float16 if device == "cuda" else torch.float32
            
            base_model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name_or_path,
                trust_remote_code=True,
                torch_dtype=dtype,
                token=os.getenv("HF_TOKEN")
            )

            # Lazy load LoRA Adapter if it exists and matches architecture
            if load_lora and model_type == "nllb" and os.path.exists(LORA_ADAPTER_PATH):
                print(f"Loading LoRA adapters for NLLB from: {LORA_ADAPTER_PATH}...")
                try:
                    model = PeftModel.from_pretrained(base_model, LORA_ADAPTER_PATH)
                except Exception as e:
                    print(f"Error loading LoRA adapter for NLLB: {e}. Falling back to base.")
                    model = base_model
            elif load_lora and model_type == "indictrans2":
                # Check for a specific IndicTrans2 LoRA adapter in target directories
                parent_dir = os.path.dirname(LORA_ADAPTER_PATH)
                indic_lora_path = os.path.join(parent_dir, "indictrans2_lora_adapter")
                if os.path.exists(indic_lora_path):
                    print(f"Loading LoRA adapters for IndicTrans2 from: {indic_lora_path}...")
                    try:
                        model = PeftModel.from_pretrained(base_model, indic_lora_path)
                    except Exception as e:
                        print(f"Error loading LoRA adapter for IndicTrans2: {e}. Falling back to base.")
                        model = base_model
                else:
                    print("No IndicTrans2 LoRA adapter found. Running base IndicTrans2 model.")
                    model = base_model
            else:
                model = base_model

            cls._models[model_key] = model.to(device)
            cls._models[model_key].eval()
            print(f"{model_type} model loaded successfully.")

        return cls._models[model_key]

    @classmethod
    def clear_memory(cls):
        """Frees up memory by running garbage collection and emptying CUDA cache."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("GPU Memory: CUDA Cache cleared.")
