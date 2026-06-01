"""
History route: GET /history (protected).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import HistoryItem, HistoryResponse
from app.services.history_service import HistoryService
from app.routes.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    skip: int = 0,
    limit: int = 50,
    user_id: str = Depends(get_current_user),
):
    """Return translation history for the authenticated user."""
    try:
        service = HistoryService()
        items, total = await service.get_history(user_id=user_id, skip=skip, limit=limit)
        return HistoryResponse(
            items=[
                HistoryItem(
                    id=it.get("id"),
                    original_text=it["original_text"],
                    translated_text=it["translated_text"],
                    src_lang=it["src_lang"],
                    target_lang=it["target_lang"],
                    timestamp=it["timestamp"],
                    audio_ref=it.get("audio_ref"),
                )
                for it in items
            ],
            total=total,
        )
    except Exception as e:
        logger.exception("History fetch failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load history")
