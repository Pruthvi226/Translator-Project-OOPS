"""
Application configuration via environment variables.
"""

import os
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized settings loaded from environment."""

    APP_NAME: str = "AI-Translator-Pro"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database (MongoDB)
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ai_translator_pro"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Optional: OpenAI/Whisper (set in .env for production)
    OPENAI_API_KEY: str = ""
    USE_WHISPER_API: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    return Settings()
