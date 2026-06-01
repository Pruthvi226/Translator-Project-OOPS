"""
Pydantic request/response schemas for API validation and serialization.
"""

from typing import Optional, List

from pydantic import BaseModel, Field


# ----- Translation -----
class TranslateRequest(BaseModel):
    """Request body for POST /translate."""

    text: str = Field(..., min_length=1, max_length=50000)
    src_lang: Optional[str] = Field("auto", description="Source language code or 'auto'")
    target_lang: str = Field("en", min_length=2, max_length=10)
    correct_grammar: bool = Field(False, description="Apply grammar correction before translation")
    learning_mode: bool = Field(False, description="Return explanation of translation")


class TranslateResponse(BaseModel):
    """Response for POST /translate."""

    translated_text: str
    detected_src_lang: Optional[str] = None
    explanation: Optional[str] = None


# ----- Speech -----
class SpeechToTextRequest(BaseModel):
    """Request for speech-to-text (multipart file or base64)."""

    language: Optional[str] = Field(None, description="Hint for source language code")


class SpeechToTextResponse(BaseModel):
    """Response for POST /speech-to-text."""

    text: str
    detected_language: Optional[str] = None


# ----- TTS -----
class TextToSpeechRequest(BaseModel):
    """Request for POST /text-to-speech."""

    text: str = Field(..., min_length=1, max_length=5000)
    lang: str = Field("en", min_length=2, max_length=10)


class TextToSpeechResponse(BaseModel):
    """Response for POST /text-to-speech."""

    audio_url: str


# ----- Image -----
class ImageTranslateResponse(BaseModel):
    """Response for POST /image-translate."""

    extracted_text: str
    translated_text: str
    detected_language: Optional[str] = None


# ----- Auth -----
class UserCreate(BaseModel):
    """Request for POST /signup."""

    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Request for POST /login."""

    email: str
    password: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


# ----- History -----
class HistoryItem(BaseModel):
    """Single history entry."""

    id: Optional[str] = None
    original_text: str
    translated_text: str
    src_lang: str
    target_lang: str
    timestamp: str
    audio_ref: Optional[str] = None


class HistoryResponse(BaseModel):
    """Response for GET /history."""

    items: List[HistoryItem]
    total: int
