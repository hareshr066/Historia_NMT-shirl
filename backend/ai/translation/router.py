from backend.ai.translation.indictrans2_engine import IndicTrans2Engine
from backend.ai.translation.nllb import NLLBModelHolder

class TranslationRouter:
    @staticmethod
    def translate(text: str, model_choice: str = "indictrans2", disable_adapter: bool = False) -> str:
        """
        Routes the translation request to the selected model provider.
        Default model: IndicTrans2.
        Backward compatibility: supports NLLB (OPUS-MT) for benchmarking/comparisons.
        """
        model_choice_clean = model_choice.lower().strip()
        
        if model_choice_clean == "nllb" or model_choice_clean == "opus-mt":
            # Route to NLLB/OPUS-MT engine for benchmarking
            return NLLBModelHolder.translate(text, disable_adapter=disable_adapter)
        elif model_choice_clean == "indictrans2":
            # Route to the new IndicTrans2 engine
            return IndicTrans2Engine.translate(text, disable_adapter=disable_adapter)
        else:
            # Default to IndicTrans2
            print(f"Model '{model_choice}' unsupported. Defaulting to IndicTrans2.")
            return IndicTrans2Engine.translate(text, disable_adapter=disable_adapter)
