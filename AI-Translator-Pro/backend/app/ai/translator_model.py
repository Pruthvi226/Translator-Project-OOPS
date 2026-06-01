"""
Translation using deep_translator (Google). Optional LLM/transformers for improved quality.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TranslatorModel:
    """
    Translates text between languages. Uses deep_translator by default.
    Can be extended with HuggingFace or LLM API for learning mode / explanations.
    """

    def __init__(self):
        pass

    def translate(self, text: str, src_lang: str, target_lang: str) -> str:
        """Translate text from src_lang to target_lang."""
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=src_lang, target=target_lang)
        return translator.translate(text)

    def detect_language(self, text: str) -> Optional[str]:
        """Detect language of text. Returns language code or None."""
        try:
            from langdetect import detect
            return detect(text)
        except ImportError:
            pass
        except Exception:
            pass
        return None

    def explain(self, translated_text: str, target_lang: str) -> Optional[str]:
        """
        Return a short explanation of the translated sentence (language learning mode).
        Optional: integrate LLM API here.
        """
        # Placeholder: could call an LLM to explain grammar/vocabulary
        return f"Translated to {target_lang}. (Enable an LLM API for detailed explanations.)"
