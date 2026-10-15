from functools import lru_cache
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    environment: str = 'development'
    database_url: str = 'sqlite:///./fluentflow.db'
    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    token_minutes: int = 60
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-3.5-flash-lite'
    provider_order: str = 'gemini'
    enable_deep_translator: bool = False
    enable_nllb: bool = False
    enable_speech: bool = False
    enable_rag: bool = False
    whisper_model: str = 'base'
    provider_timeout: float = Field(30, ge=1, le=120)
    provider_retries: int = Field(1, ge=0, le=3)
    rate_limit: int = Field(30, ge=1)
    max_upload_mb: int = Field(10, ge=1, le=25)
    retention_days: int = Field(30, ge=1)
    cors_origins: str = 'http://localhost:5173'
    frontend_dist: str = ''
    gemini_input_usd_per_million: float | None = None
    gemini_output_usd_per_million: float | None = None

    @field_validator('database_url', mode='before')
    @classmethod
    def postgres_driver(cls, value):
        for prefix in ('postgres://', 'postgresql://'):
            if value.startswith(prefix):
                return 'postgresql+psycopg://' + value[len(prefix):]
        return value

    @model_validator(mode='after')
    def production(self):
        if self.environment == 'production':
            if len(self.jwt_secret) < 32 or self.jwt_secret.startswith('change'):
                raise ValueError('A strong JWT_SECRET is required')
            if 'jwt_secret' not in self.model_fields_set:
                raise ValueError('Set JWT_SECRET explicitly in production')
            if not self.database_url.startswith('postgresql'):
                raise ValueError('Production requires PostgreSQL')
        return self


@lru_cache
def get_settings():
    return Settings()
