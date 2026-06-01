"""
Language validation for translation and TTS.
Uses supported language sets from deep_translator and gTTS.
"""

import logging
from typing import Set

logger = logging.getLogger(__name__)

# Common codes supported by both translation and TTS (subset)
SUPPORTED_TRANSLATION = {
    "af", "am", "ar", "az", "be", "bg", "bn", "bs", "ca", "co", "cs", "cy", "da", "de", "el", "en",
    "eo", "es", "et", "eu", "fa", "fi", "fr", "fy", "ga", "gd", "gl", "gu", "ha", "he", "hi", "hr",
    "ht", "hu", "hy", "id", "ig", "is", "it", "ja", "ka", "kk", "km", "kn", "ko", "ku", "ky", "la",
    "lb", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "no",
    "ny", "pa", "pl", "ps", "pt", "ro", "ru", "sd", "si", "sk", "sl", "sm", "sn", "so", "sq", "sr",
    "st", "su", "sv", "sw", "ta", "te", "tg", "th", "tl", "tr", "uk", "ur", "uz", "vi", "xh", "yi",
    "yo", "zh-cn", "zh-tw", "zu",
}


def _get_tts_langs() -> Set[str]:
    """Lazy load gTTS supported languages."""
    try:
        from gtts.lang import tts_langs
        return set(tts_langs().keys())
    except Exception as e:
        logger.warning("gTTS langs unavailable: %s", e)
        return set()


class LanguageHandler:
    """Validates language codes for translation and TTS."""

    def __init__(self):
        self._tts_langs: Set[str] | None = None

    @property
    def tts_langs(self) -> Set[str]:
        if self._tts_langs is None:
            self._tts_langs = _get_tts_langs()
        return self._tts_langs

    def validate_source_language(self, lang: str) -> None:
        if lang != "auto" and lang not in SUPPORTED_TRANSLATION:
            raise ValueError(f"Unsupported source language: {lang}")

    def validate_target_language(self, lang: str) -> None:
        if lang not in SUPPORTED_TRANSLATION:
            raise ValueError(f"Unsupported target language: {lang}")

    def validate_tts_language(self, lang: str) -> None:
        if lang not in self.tts_langs and lang not in SUPPORTED_TRANSLATION:
            raise ValueError(f"Unsupported TTS language: {lang}")
