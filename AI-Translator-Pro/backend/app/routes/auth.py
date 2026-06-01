"""
Auth routes: POST /login, POST /signup.
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from jose import jwt

from app.models.schemas import UserCreate, UserLogin, Token
from app.utils.config import get_settings
from app.services.user_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter()


def _create_access_token(sub: str) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": sub, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@router.post("/signup", response_model=Token)
async def signup(body: UserCreate):
    """Register a new user. Returns JWT access token."""
    try:
        service = UserService()
        user = await service.create_user(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
        token = _create_access_token(sub=user["id"])
        return Token(access_token=token, token_type="bearer")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Signup failed: %s", e)
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=Token)
async def login(body: UserLogin):
    """Authenticate user and return JWT access token."""
    try:
        service = UserService()
        user = await service.authenticate(body.email, body.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = _create_access_token(sub=user["id"])
        return Token(access_token=token, token_type="bearer")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Login failed: %s", e)
        raise HTTPException(status_code=500, detail="Login failed")
