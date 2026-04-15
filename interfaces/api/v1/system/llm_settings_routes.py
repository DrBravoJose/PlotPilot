from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from interfaces.api.dependencies import get_llm_settings_service, get_openai_oauth_service


router = APIRouter(prefix="/settings", tags=["llm-settings"])


class LlmSettingsPatch(BaseModel):
    current_provider: str | None = None
    provider_settings: dict[str, dict[str, Any]] = {}


@router.get("/llm")
def get_llm_settings(
    service=Depends(get_llm_settings_service),
    oauth=Depends(get_openai_oauth_service),
):
    return service.get_settings(oauth_status=oauth.get_status())


@router.get("/llm/registry")
def get_llm_registry(service=Depends(get_llm_settings_service)):
    return service.get_registry()


@router.put("/llm")
def update_llm_settings(
    payload: LlmSettingsPatch,
    service=Depends(get_llm_settings_service),
    oauth=Depends(get_openai_oauth_service),
):
    service.update_settings(payload.model_dump(exclude_none=True))
    return service.get_settings(oauth_status=oauth.get_status())
