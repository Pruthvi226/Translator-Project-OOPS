"""
History service: fetch user translation history from DB.
"""

import logging
from typing import List, Tuple

from app.database.db import get_db

logger = logging.getLogger(__name__)


class HistoryService:
    """Retrieves translation history for a user."""

    async def get_history(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[dict], int]:
        """Return (list of history items, total count)."""
        db = await get_db()
        items = await db.get_translations(user_id=user_id, skip=skip, limit=limit)
        total = await db.count_translations(user_id=user_id)
        return items, total
