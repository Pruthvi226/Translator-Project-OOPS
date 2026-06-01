"""
OCR: extract text from images using pytesseract.
"""

import logging
from typing import BinaryIO

logger = logging.getLogger(__name__)


class OCRModel:
    """Extracts text from images using Tesseract OCR."""

    def __init__(self):
        pass

    def extract_text(self, image_stream: BinaryIO) -> str:
        """
        Extract text from image. Returns empty string if OCR fails or no text found.
        """
        try:
            import pytesseract
            from PIL import Image
            image_stream.seek(0)
            img = Image.open(image_stream)
            text = pytesseract.image_to_string(img)
            return (text or "").strip()
        except ImportError as e:
            logger.warning("pytesseract or PIL not installed: %s", e)
            return ""
        except Exception as e:
            logger.exception("OCR failed: %s", e)
            return ""
