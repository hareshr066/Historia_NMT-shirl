import os
import torch
import time
from typing import List
from backend.core.config import (
    TRANSLATION_MODEL_NAME, 
    TRANSLATION_SOURCE_LANG, 
    TRANSLATION_TARGET_LANG,
    TRANSLATION_BEAM_SIZE,
    TRANSLATION_MAX_LENGTH
)
from backend.core.model_loader import ModelLoader
from backend.ai.translation.indictrans2_processor import IndicProcessor

class IndicTrans2Engine:
    _processor = None

    @classmethod
    def get_processor(cls) -> IndicProcessor:
        if cls._processor is None:
            cls._processor = IndicProcessor(inference=True)
        return cls._processor

    @classmethod
    def translate(
        cls, 
        text: str, 
        disable_adapter: bool = False, 
        src_lang: str = TRANSLATION_SOURCE_LANG, 
        tgt_lang: str = TRANSLATION_TARGET_LANG
    ) -> str:
        """
        Translates a single input sentence using IndicTrans2.
        """
        if not text or not text.strip():
            return ""
            
        results = cls.translate_batch([text], disable_adapter=disable_adapter, src_lang=src_lang, tgt_lang=tgt_lang)
        return results[0] if results else ""

    @classmethod
    def translate_batch(
        cls, 
        texts: List[str], 
        disable_adapter: bool = False, 
        src_lang: str = TRANSLATION_SOURCE_LANG, 
        tgt_lang: str = TRANSLATION_TARGET_LANG
    ) -> List[str]:
        """
        Translates a batch of input sentences using IndicTrans2.
        """
        if not texts:
            return []

        # 1. Load model and tokenizer via lazy-loading ModelLoader singleton
        tokenizer = ModelLoader.load_tokenizer("indictrans2", TRANSLATION_MODEL_NAME)
        # Note: we pass not disable_adapter as load_lora parameter to load lora
        model = ModelLoader.load_model("indictrans2", TRANSLATION_MODEL_NAME, load_lora=not disable_adapter)
        device = ModelLoader.get_device("indictrans2")

        # 2. Preprocess batch
        ip = cls.get_processor()
        batch = ip.preprocess_batch(texts, src_lang=src_lang, tgt_lang=tgt_lang)

        # 3. Tokenize sentences
        inputs = tokenizer(
            batch, 
            truncation=True, 
            padding="longest", 
            return_tensors="pt",
            return_attention_mask=True
        ).to(device)

        # 4. Generate translations
        with torch.no_grad():
            if disable_adapter and hasattr(model, "disable_adapter"):
                with model.disable_adapter():
                    generated_tokens = model.generate(
                        **inputs,
                        use_cache=True,
                        min_length=0,
                        max_length=TRANSLATION_MAX_LENGTH,
                        num_beams=TRANSLATION_BEAM_SIZE,
                        num_return_sequences=1
                    )
            else:
                generated_tokens = model.generate(
                    **inputs,
                    use_cache=True,
                    min_length=0,
                    max_length=TRANSLATION_MAX_LENGTH,
                    num_beams=TRANSLATION_BEAM_SIZE,
                    num_return_sequences=1
                )

        # 5. Decode generated tokens
        decoded_tokens = tokenizer.batch_decode(
            generated_tokens, 
            skip_special_tokens=True, 
            clean_up_tokenization_spaces=True
        )

        # 6. Postprocess translations
        translations = ip.postprocess_batch(decoded_tokens, lang=tgt_lang)
        return translations
