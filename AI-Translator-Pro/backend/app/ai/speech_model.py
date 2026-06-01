"""
Speech-to-text using OpenAI Whisper (local or API).
Falls back to no-op / placeholder if Whisper not installed.
"""

import logging
from typing import Optional, BinaryIO

logger = logging.getLogger(__name__)


class SpeechModel:
    """
    Transcribes audio to text using Whisper.
    Set USE_WHISPER_API=True and OPENAI_API_KEY for API; otherwise uses local whisper.
    """

    def __init__(self):
        self._model = None
        self._use_api = False
        try:
            from app.utils.config import get_settings
            s = get_settings()
            self._use_api = getattr(s, "USE_WHISPER_API", False) and bool(getattr(s, "OPENAI_API_KEY", ""))
        except Exception:
            pass

    def transcribe(
        self,
        audio_stream: BinaryIO,
        language: Optional[str] = None,
    ) -> dict:
        """
        Returns dict with 'text' and optional 'language'.
        If Whisper unavailable, returns placeholder text.
        """
        if self._use_api:
            return self._transcribe_api(audio_stream, language)
        return self._transcribe_local(audio_stream, language)

    def _transcribe_api(self, audio_stream: BinaryIO, language: Optional[str]) -> dict:
        try:
            import openai
            from app.utils.config import get_settings
            openai.api_key = get_settings().OPENAI_API_KEY
            audio_stream.seek(0)
            # OpenAI expects file-like with name for format
            response = openai.Audio.transcribe("whisper-1", audio_stream, language=language or None)
            text = response.get("text", "")
            return {"text": text, "language": language}
        except Exception as e:
            logger.warning("Whisper API failed: %s", e)
            return {"text": "[Speech recognition unavailable]", "language": None}

    def _transcribe_local(self, audio_stream: BinaryIO, language: Optional[str]) -> dict:
        try:
            import whisper
            if self._model is None:
                self._model = whisper.load_model("base")
            audio_stream.seek(0)
            # whisper.load_audio expects file path or bytes
            import numpy as np
            data = audio_stream.read()
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(data)
                path = f.name
            try:
                result = self._model.transcribe(path, language=language, fp16=False)
                text = result.get("text", "").strip()
                lang = result.get("language")
                return {"text": text, "language": lang}
            finally:
                import os
                try:
                    os.unlink(path)
                except Exception:
                    pass
        except ImportError:
            logger.warning("Whisper not installed; install with: pip install openai-whisper")
            return {"text": "[Install Whisper for speech recognition]", "language": None}
        except Exception as e:
            logger.exception("Local Whisper failed: %s", e)
            return {"text": "[Transcription failed]", "language": None}
