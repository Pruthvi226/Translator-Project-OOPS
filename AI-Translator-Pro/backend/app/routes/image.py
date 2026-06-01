"""
Image translation route: POST /image-translate.
Upload image -> OCR -> translate extracted text.
"""

import logging
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import ImageTranslateResponse
from app.services.image_translate_service import ImageTranslateService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/image-translate", response_model=ImageTranslateResponse)
async def image_translate(
    file: UploadFile = File(...),
    target_lang: str = Form("en"),
):
    """
    Extract text from image via OCR, then translate to target language.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image (e.g. PNG, JPEG)")
    try:
        contents = await file.read()
        service = ImageTranslateService()
        result = await service.process(contents, target_lang=target_lang)
        return ImageTranslateResponse(
            extracted_text=result["extracted_text"],
            translated_text=result["translated_text"],
            detected_language=result.get("detected_language"),
        )
    except Exception as e:
        logger.exception("Image translate failed: %s", e)
        raise HTTPException(status_code=500, detail="Image translation failed")
