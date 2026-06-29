import os
import torch
from backend.core.config import NLL_MODEL_PATH, SOURCE_LANG, TARGET_LANG
from backend.core.model_loader import ModelLoader

class NLLBModelHolder:
    @classmethod
    def translate(cls, text: str, disable_adapter: bool = False) -> str:
        """
        Translates text using NLLB base model or fine-tuned LoRA adapters (for backward compatibility).
        Uses the centralized ModelLoader singleton.
        """
        tokenizer = ModelLoader.load_tokenizer("nllb", NLL_MODEL_PATH)
        model = ModelLoader.load_model("nllb", NLL_MODEL_PATH, load_lora=not disable_adapter)
        device = ModelLoader.get_device("nllb")

        # Configure translation languages on the tokenizer
        tokenizer.src_lang = SOURCE_LANG
        tokenizer.tgt_lang = TARGET_LANG

        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256).to(device)
        
        with torch.no_grad():
            if disable_adapter and hasattr(model, "disable_adapter"):
                with model.disable_adapter():
                    outputs = model.generate(**inputs, max_length=256, num_beams=5)
            else:
                outputs = model.generate(**inputs, max_length=256, num_beams=5)
                
        return tokenizer.batch_decode(outputs, skip_special_tokens=True)[0].strip()
