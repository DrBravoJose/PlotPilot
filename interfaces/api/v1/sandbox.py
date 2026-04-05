"""Sandbox API endpoints for dialogue whitelist and simulation."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from application.services.sandbox_dialogue_service import SandboxDialogueService
from application.dtos.sandbox_dto import DialogueWhitelistResponse
from interfaces.api.dependencies import get_sandbox_dialogue_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/novels", tags=["sandbox"])


@router.get("/{novel_id}/sandbox/dialogue-whitelist", response_model=DialogueWhitelistResponse)
async def get_dialogue_whitelist(
    novel_id: str,
    chapter_number: Optional[int] = Query(None, ge=1, description="Filter by chapter number"),
    speaker: Optional[str] = Query(None, description="Filter by speaker name"),
    service: SandboxDialogueService = Depends(get_sandbox_dialogue_service)
) -> DialogueWhitelistResponse:
    """
    Get dialogue whitelist for sandbox simulation.

    This endpoint retrieves all dialogues available for sandbox scenario planning,
    with optional filters for chapter and speaker.

    Args:
        novel_id: The novel ID
        chapter_number: Optional chapter filter (must be >= 1)
        speaker: Optional speaker name filter
        service: Injected sandbox dialogue service

    Returns:
        DialogueWhitelistResponse containing filtered dialogues

    Raises:
        HTTPException: 500 if internal error occurs
    """
    try:
        result = service.get_dialogue_whitelist(
            novel_id=novel_id,
            chapter_number=chapter_number,
            speaker=speaker
        )
        return result

    except Exception as e:
        logger.error(f"Error retrieving dialogue whitelist: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
