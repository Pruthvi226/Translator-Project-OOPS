"""
MongoDB connection and collections for users and translations.
Async-ready interface; use motor in production.
"""

import logging
from datetime import datetime
from typing import List, Optional

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

# In-memory fallback when MongoDB is not available (e.g. dev without DB)
_memory_users: dict = {}
_memory_translations: list = []
_memory_id = 0


def _next_id() -> str:
    global _memory_id
    _memory_id += 1
    return str(_memory_id)


class Database:
    """
    Database abstraction: MongoDB with in-memory fallback.
    Replace with motor AsyncIOMotorClient in production.
    """

    def __init__(self):
        self._client = None
        self._db = None
        self._users = None
        self._translations = None

    async def _ensure_connected(self):
        if self._db is not None:
            return
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            settings = get_settings()
            self._client = AsyncIOMotorClient(settings.MONGODB_URI)
            self._db = self._client[settings.MONGODB_DB_NAME]
            self._users = self._db["users"]
            self._translations = self._db["translations"]
            await self._users.create_index("email", unique=True)
            await self._translations.create_index([("user_id", 1), ("timestamp", -1)])
        except Exception as e:
            logger.warning("MongoDB not available, using in-memory store: %s", e)
            self._db = "memory"

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        full_name: str = "",
    ) -> str:
        await self._ensure_connected()
        if self._db == "memory":
            uid = _next_id()
            _memory_users[email] = {
                "id": uid,
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
            }
            return uid
        from bson.objectid import ObjectId
        r = await self._users.insert_one({
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
        })
        return str(r.inserted_id)

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        await self._ensure_connected()
        if self._db == "memory":
            return _memory_users.get(email)
        doc = await self._users.find_one({"email": email})
        if not doc:
            return None
        doc["id"] = str(doc["_id"])
        doc["hashed_password"] = doc.get("hashed_password", "")
        return doc

    async def save_translation(
        self,
        user_id: str,
        original_text: str,
        translated_text: str,
        src_lang: str,
        target_lang: str,
        audio_ref: Optional[str] = None,
    ) -> None:
        await self._ensure_connected()
        entry = {
            "user_id": user_id,
            "original_text": original_text,
            "translated_text": translated_text,
            "src_lang": src_lang,
            "target_lang": target_lang,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "audio_ref": audio_ref,
        }
        if self._db == "memory":
            entry["id"] = _next_id()
            _memory_translations.append(entry)
            return
        from bson.objectid import ObjectId
        await self._translations.insert_one(entry)

    async def get_translations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        await self._ensure_connected()
        if self._db == "memory":
            filtered = [t for t in _memory_translations if t.get("user_id") == user_id]
            filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            page = filtered[skip : skip + limit]
            for t in page:
                t.setdefault("id", t.get("id"))
            return page
        cursor = self._translations.find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(limit)
        items = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            items.append(doc)
        return items

    async def count_translations(self, user_id: str) -> int:
        await self._ensure_connected()
        if self._db == "memory":
            return sum(1 for t in _memory_translations if t.get("user_id") == user_id)
        return await self._translations.count_documents({"user_id": user_id})


_db_instance: Optional[Database] = None


async def get_db() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
