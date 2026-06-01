"""
Speech-to-text service using Whisper (or fallback).
"""

import io
import logging
from typing import Optional

from app.ai.speech_model import SpeechModel

logger = logging.getLogger(__name__)


class SpeechService:
    """Converts audio bytes to text using AI speech recognition."""

    def __init__(self):
        self.speech_model = SpeechModel()

    async def speech_to_text(
        self,
        audio_bytes: bytes,
        language_hint: Optional[str] = None,
    ) -> dict:
        """
        Transcribe audio to text.
        Returns dict with 'text' and optional 'detected_language'.
        """
        result = self.speech_model.transcribe(io.BytesIO(audio_bytes), language=language_hint)
        return {"text": result.get("text", ""), "detected_language": result.get("language")}
