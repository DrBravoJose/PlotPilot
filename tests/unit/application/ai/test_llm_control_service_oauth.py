from __future__ import annotations

import pytest

from application.ai.llm_control_service import LLMControlService, LLMProfile
from domain.ai.services.llm_service import GenerationResult
from domain.ai.value_objects.token_usage import TokenUsage


class _StubProvider:
    async def generate(self, prompt, config):
        return GenerationResult(
            content="codex ok",
            token_usage=TokenUsage(input_tokens=0, output_tokens=0),
        )


@pytest.mark.anyio
async def test_test_profile_model_allows_openai_oauth_without_api_key():
    service = LLMControlService()
    profile = LLMProfile(
        id="openai-oauth",
        name="OpenAI 官方",
        preset_key="openai-official",
        protocol="openai",
        base_url="https://api.openai.com/v1",
        api_key="",
        auth_mode="oauth",
        model="gpt-5.4",
    )

    result = await service.test_profile_model(profile, lambda _: _StubProvider())

    assert result.ok is True
    assert result.preview == "codex ok"
