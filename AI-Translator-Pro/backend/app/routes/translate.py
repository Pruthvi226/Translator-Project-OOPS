"""
Translation route: POST /translate.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import TranslateRequest, TranslateResponse
from app.services.translation_service import TranslationService
from app.routes.deps import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/translate", response_model=TranslateResponse)
async def translate(
    body: TranslateRequest,
    user_id: str | None = Depends(get_current_user_optional),
):
    """
    Translate text from source language to target language.
    Supports auto language detection, optional grammar correction, and learning mode.
    """
    try:
        service = TranslationService()
        result = await service.translate(
            text=body.text,
            src_lang=body.src_lang or "auto",
            target_lang=body.target_lang,
            correct_grammar=body.correct_grammar,
            learning_mode=body.learning_mode,
            user_id=user_id,
        )
        return TranslateResponse(
            translated_text=result["translated_text"],
            detected_src_lang=result.get("detected_src_lang"),
            explanation=result.get("explanation"),
        )
    except ValueError as e:
        logger.warning("Validation error in translate: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Translation failed: %s", e)
        raise HTTPException(status_code=500, detail="Translation failed")
