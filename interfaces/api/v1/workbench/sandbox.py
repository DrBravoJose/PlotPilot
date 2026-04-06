"""Sandbox API endpoints for dialogue whitelist and simulation."""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from application.workbench.services.sandbox_dialogue_service import SandboxDialogueService
from application.workbench.dtos.sandbox_dto import DialogueWhitelistResponse
from interfaces.api.dependencies import get_sandbox_dialogue_service, get_bible_service, get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/novels", tags=["sandbox"])


class CharacterAnchorResponse(BaseModel):
    """角色心理锚点响应"""
    character_id: str
    character_name: str
    mental_state: str
    verbal_tic: str
    idle_behavior: str


class GenerateDialogueRequest(BaseModel):
    """生成对话请求"""
    novel_id: str
    character_id: str
    scene_prompt: str
    mental_state: Optional[str] = None
    verbal_tic: Optional[str] = None


class GenerateDialogueResponse(BaseModel):
    """生成对话响应"""
    dialogue: str
    character_name: str


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


@router.get("/{novel_id}/sandbox/character/{character_id}/anchor", response_model=CharacterAnchorResponse)
async def get_character_anchor(
    novel_id: str,
    character_id: str,
    bible_service = Depends(get_bible_service)
):
    """
    获取角色心理锚点数据

    返回角色的心理状态、口头禅、待机动作等锚点信息
    """
    try:
        # 从 Bible 获取角色信息
        bible = bible_service.get_bible_by_novel(novel_id)

        if not bible:
            raise HTTPException(status_code=404, detail=f"Bible not found for novel {novel_id}")

        # 查找指定角色
        character = None
        for char in bible.characters:
            if char.id == character_id:
                character = char
                break

        if not character:
            raise HTTPException(status_code=404, detail=f"Character {character_id} not found")

        # 提取心理锚点（从角色描述中解析，或使用默认值）
        # 注意：Character 实体只有 id, name, description, relationships 字段
        # 这里返回基于角色名称的默认锚点数据
        return CharacterAnchorResponse(
            character_id=character_id,
            character_name=character.name,
            mental_state="平静",
            verbal_tic="...",
            idle_behavior="思考"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching character anchor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch character anchor")


@router.post("/sandbox/generate-dialogue", response_model=GenerateDialogueResponse)
async def generate_dialogue(
    request: GenerateDialogueRequest,
    bible_service = Depends(get_bible_service),
    llm_service = Depends(get_llm_service)
):
    """
    AI 生成对话

    根据角色锚点和场景描述，生成符合角色特征的对话
    """
    try:
        # 获取角色信息
        character = bible_service.get_character(request.novel_id, request.character_id)

        if not character:
            raise HTTPException(status_code=404, detail=f"Character {request.character_id} not found")

        character_name = character.get("name", request.character_id)

        # 构建 prompt
        mental_state = request.mental_state or "平静"
        verbal_tic = request.verbal_tic or ""

        prompt = f"""你是一位专业的对话编剧。请根据以下信息生成一段对话：

角色：{character_name}
心理状态：{mental_state}
口头禅：{verbal_tic}
场景：{request.scene_prompt}

要求：
1. 对话要符合角色的心理状态和性格特征
2. 自然融入口头禅（如果有）
3. 对话长度控制在 2-4 句话
4. 只返回对话内容，不要加任何说明

对话："""

        # 调用 LLM 生成
        response = await llm_service.generate(prompt, max_tokens=200)
        dialogue = response.strip()

        return GenerateDialogueResponse(
            dialogue=dialogue,
            character_name=character_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating dialogue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate dialogue")

