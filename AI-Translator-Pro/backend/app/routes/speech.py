"""
Speech-to-text route: POST /speech-to-text.
Accepts multipart file (audio) and optional language hint.
"""

import logging
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import SpeechToTextResponse
from app.services.speech_service import SpeechService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    language: str | None = Form(None),
):
    """
    Convert speech audio to text using Whisper (or fallback).
    Accepts: WAV, MP3, WebM, etc.
    """
    if not file.content_type or not file.content_type.startswith("audio/"):
        if not file.filename or not any(
            file.filename.lower().endswith(ext) for ext in (".wav", ".mp3", ".webm", ".ogg", ".m4a")
        ):
            raise HTTPException(400, "File must be an audio type (e.g. WAV, MP3)")
    try:
        contents = await file.read()
        service = SpeechService()
        result = await service.speech_to_text(contents, language_hint=language)
        return SpeechToTextResponse(
            text=result["text"],
            detected_language=result.get("detected_language"),
        )
    except Exception as e:
        logger.exception("Speech-to-text failed: %s", e)
        raise HTTPException(status_code=500, detail="Speech recognition failed")
