"""
Text-to-speech using gTTS (Google TTS). Saves to file path.
"""

import logging

logger = logging.getLogger(__name__)


class TTSModel:
    """Synthesizes speech from text and saves to MP3 file."""

    def __init__(self):
        pass

    def synthesize(self, text: str, output_path: str, lang: str = "en") -> None:
        """Generate MP3 at output_path."""
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang)
        tts.save(output_path)
