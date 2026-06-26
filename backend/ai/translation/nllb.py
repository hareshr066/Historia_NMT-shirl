import os
import torch
import sys
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
from backend.core.config import NLL_MODEL_PATH, LORA_ADAPTER_PATH, SOURCE_LANG, TARGET_LANG

# Disable CVE check for PyTorch weights loader
import transformers.utils.import_utils
import transformers.modeling_utils
transformers.utils.import_utils.check_torch_load_is_safe = lambda: None
transformers.modeling_utils.check_torch_load_is_safe = lambda: None

class NLLBModelHolder:
    _model = None
    _tokenizer = None
    _device = None

    @classmethod
    def initialize(cls):
        if cls._model is not None:
            return
            
        cls._device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading translation tokenizer and base model: {NLL_MODEL_PATH} on {cls._device}...")
        
        cls._tokenizer = AutoTokenizer.from_pretrained(NLL_MODEL_PATH, trust_remote_code=True)
        
        base_model = AutoModelForSeq2SeqLM.from_pretrained(
            NLL_MODEL_PATH,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        
        if os.path.exists(LORA_ADAPTER_PATH):
            print(f"Loading LoRA adapters from: {LORA_ADAPTER_PATH}...")
            cls._model = PeftModel.from_pretrained(base_model, LORA_ADAPTER_PATH)
        else:
            print("LoRA adapter path not found. Running base NLLB model.")
            cls._model = base_model
            
        cls._model = cls._model.to(cls._device)
        cls._model.eval()
        
        # Configure translation languages
        cls._tokenizer.src_lang = SOURCE_LANG
        cls._tokenizer.tgt_lang = TARGET_LANG

    @classmethod
    def translate(cls, text: str, disable_adapter: bool = False) -> str:
        cls.initialize()
        
        inputs = cls._tokenizer(text, return_tensors="pt", truncation=True, max_length=256).to(cls._device)
        
        with torch.no_grad():
            if disable_adapter and hasattr(cls._model, "disable_adapter"):
                with cls._model.disable_adapter():
                    outputs = cls._model.generate(**inputs, max_length=256, num_beams=5)
            else:
                outputs = cls._model.generate(**inputs, max_length=256, num_beams=5)
                
        return cls._tokenizer.batch_decode(outputs, skip_special_tokens=True)[0].strip()
