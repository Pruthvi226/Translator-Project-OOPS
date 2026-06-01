"""
Translation service: orchestrates grammar correction, translation, learning mode.
Saves history when user_id is present.
"""

import logging
from typing import Optional

from app.ai.translator_model import TranslatorModel
from app.ai.grammar_model import GrammarModel
from app.database.db import get_db
from app.utils.language_handler import LanguageHandler

logger = logging.getLogger(__name__)


class TranslationService:
    """Orchestrates translation with optional grammar correction and learning mode."""

    def __init__(self):
        self.translator = TranslatorModel()
        self.grammar = GrammarModel()
        self.lang_handler = LanguageHandler()

    async def translate(
        self,
        text: str,
        src_lang: str = "auto",
        target_lang: str = "en",
        correct_grammar: bool = False,
        learning_mode: bool = False,
        user_id: Optional[str] = None,
    ) -> dict:
        """
        Translate text. Optionally correct grammar first and add explanation.
        Returns dict with translated_text, detected_src_lang, explanation.
        """
        self.lang_handler.validate_target_language(target_lang)
        text_to_translate = text
        if correct_grammar:
            text_to_translate = self.grammar.correct(text)
        detected_src = None
        if src_lang == "auto":
            detected_src = self.translator.detect_language(text_to_translate)
            src_lang = detected_src or "en"
        self.lang_handler.validate_source_language(src_lang)
        translated = self.translator.translate(text_to_translate, src_lang, target_lang)
        explanation = None
        if learning_mode:
            explanation = self.translator.explain(translated, target_lang)
        if user_id:
            await self._save_history(
                user_id=user_id,
                original_text=text,
                translated_text=translated,
                src_lang=src_lang,
                target_lang=target_lang,
            )
        return {
            "translated_text": translated,
            "detected_src_lang": detected_src,
            "explanation": explanation,
        }

    async def _save_history(
        self,
        user_id: str,
        original_text: str,
        translated_text: str,
        src_lang: str,
        target_lang: str,
        audio_ref: Optional[str] = None,
    ) -> None:
        """Persist translation to history (fire-and-forget)."""
        try:
            db = await get_db()
            await db.save_translation(
                user_id=user_id,
                original_text=original_text,
                translated_text=translated_text,
                src_lang=src_lang,
                target_lang=target_lang,
                audio_ref=audio_ref,
            )
        except Exception as e:
            logger.warning("Failed to save history: %s", e)
