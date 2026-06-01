"""
FastAPI main application entry point.
Modular routes, CORS, logging, and exception handlers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, history, translate, speech, tts, image
from app.utils.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting AI-Translator-Pro API")
    yield
    logger.info("Shutting down AI-Translator-Pro API")


app = FastAPI(
    title="AI-Translator-Pro API",
    description="Production-quality AI Translation SaaS - REST API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(translate.router, prefix="/api/v1", tags=["Translation"])
app.include_router(speech.router, prefix="/api/v1", tags=["Speech"])
app.include_router(tts.router, prefix="/api/v1", tags=["TTS"])
app.include_router(image.router, prefix="/api/v1", tags=["Image"])
app.include_router(history.router, prefix="/api/v1", tags=["History"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])


@app.get("/health")
async def health_check():
    """Health check endpoint for deployment."""
    return {"status": "ok", "service": "ai-translator-pro"}
