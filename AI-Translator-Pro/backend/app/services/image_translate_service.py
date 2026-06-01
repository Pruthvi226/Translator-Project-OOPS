"""
Image translation service: OCR + translate.
"""

import io
import logging
from typing import Optional

from app.ai.ocr_model import OCRModel
from app.ai.translator_model import TranslatorModel

logger = logging.getLogger(__name__)


class ImageTranslateService:
    """Extract text from image and translate."""

    def __init__(self):
        self.ocr = OCRModel()
        self.translator = TranslatorModel()

    async def process(self, image_bytes: bytes, target_lang: str = "en") -> dict:
        """
        Run OCR on image, then translate extracted text.
        Returns dict with extracted_text, translated_text, detected_language.
        """
        extracted = self.ocr.extract_text(io.BytesIO(image_bytes))
        if not extracted.strip():
            return {
                "extracted_text": "",
                "translated_text": "",
                "detected_language": None,
            }
        detected = self.translator.detect_language(extracted)
        src_lang = detected or "en"
        translated = self.translator.translate(extracted, src_lang, target_lang)
        return {
            "extracted_text": extracted,
            "translated_text": translated,
            "detected_language": detected,
        }
