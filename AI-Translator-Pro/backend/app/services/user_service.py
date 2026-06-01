"""
User service: create and authenticate users (MongoDB).
"""

import logging
from typing import Optional

from passlib.context import CryptContext

from app.database.db import get_db

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """User registration and authentication."""

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> dict:
        """Create user. Raises ValueError if email already exists."""
        db = await get_db()
        existing = await db.get_user_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        hashed = pwd_context.hash(password)
        user_id = await db.create_user(
            email=email,
            hashed_password=hashed,
            full_name=full_name or "",
        )
        return {"id": user_id, "email": email}

    async def authenticate(self, email: str, password: str) -> Optional[dict]:
        """Verify credentials. Returns user dict with 'id' if valid."""
        db = await get_db()
        user = await db.get_user_by_email(email)
        if not user:
            return None
        if not pwd_context.verify(password, user["hashed_password"]):
            return None
        return {"id": user["id"], "email": user["email"]}
