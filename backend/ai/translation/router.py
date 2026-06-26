from backend.ai.translation.nllb import NLLBModelHolder

class TranslationRouter:
    @staticmethod
    def translate(text: str, model_choice: str = "nllb", disable_adapter: bool = False) -> str:
        """
        Routes the translation request to the selected model provider.
        Modular architecture: easily expandable to other models (IndicTrans2, Llama, Qwen, etc.).
        """
        model_choice_clean = model_choice.lower().strip()
        
        if model_choice_clean == "nllb" or model_choice_clean == "opus-mt":
            # Delegate to our NLLB module
            return NLLBModelHolder.translate(text, disable_adapter=disable_adapter)
        else:
            # Fallback/default to NLLB-200
            print(f"Model '{model_choice}' not yet fully loaded or unsupported. Defaulting to NLLB.")
            return NLLBModelHolder.translate(text, disable_adapter=disable_adapter)
