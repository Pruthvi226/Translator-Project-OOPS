"""
TTS service: generates MP3 and returns file ID for serving.
"""

import logging
import uuid
from pathlib import Path

from app.ai.tts_model import TTSModel
from app.utils.language_handler import LanguageHandler

logger = logging.getLogger(__name__)

# Directory to store generated TTS files (configurable via env in production)
TTS_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "tts"


class TTSService:
    """Generates and serves TTS audio files."""

    def __init__(self):
        self.tts = TTSModel()
        self.lang_handler = LanguageHandler()
        TTS_DIR.mkdir(parents=True, exist_ok=True)

    async def generate(self, text: str, lang: str) -> str:
        """
        Generate TTS MP3 and save to disk. Returns file_id (filename without path).
        """
        self.lang_handler.validate_tts_language(lang)
        file_id = f"{uuid.uuid4().hex}.mp3"
        path = TTS_DIR / file_id
        self.tts.synthesize(text, str(path), lang=lang)
        return file_id

    def get_file_path(self, file_id: str) -> str | None:
        """Return full path for file_id if it exists."""
        if ".." in file_id or "/" in file_id:
            return None
        p = TTS_DIR / file_id
        return str(p) if p.exists() else None
