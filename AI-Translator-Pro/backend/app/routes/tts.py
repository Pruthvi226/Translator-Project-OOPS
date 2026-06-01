"""
Text-to-speech route: POST /text-to-speech, GET /tts/file/{file_id}.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import TextToSpeechRequest, TextToSpeechResponse
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/text-to-speech", response_model=TextToSpeechResponse)
async def text_to_speech(body: TextToSpeechRequest):
    """
    Generate TTS audio from text and return URL to the generated file.
    """
    try:
        service = TTSService()
        file_id = await service.generate(body.text, body.lang)
        return TextToSpeechResponse(audio_url=f"/api/v1/tts/file/{file_id}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("TTS failed: %s", e)
        raise HTTPException(status_code=500, detail="TTS generation failed")


@router.get("/tts/file/{file_id}")
async def serve_tts_file(file_id: str):
    """Serve generated TTS MP3 file by ID."""
    service = TTSService()
    path = service.get_file_path(file_id)
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path, media_type="audio/mpeg")
