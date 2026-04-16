from unittest.mock import patch

from application.ai.llm_control_service import LLMProfile
from infrastructure.ai.provider_factory import LLMProviderFactory
from infrastructure.ai.providers.mock_provider import MockProvider


class _StubControlService:
    def resolve_profile(self, profile: LLMProfile) -> LLMProfile:
        return profile


class _StubOauthService:
    def __init__(self, status: str, token: str | None):
        self._status = status
        self._token = token

    def get_status(self) -> dict:
        return {"status": self._status}

    def get_access_token(self) -> str | None:
        return self._token


def test_create_from_profile_uses_oauth_token_for_openai_profile():
    profile = LLMProfile(
        id="openai-oauth",
        name="OpenAI OAuth",
        preset_key="openai-official",
        protocol="openai",
        api_key="",
        model="gpt-5.4",
        auth_mode="oauth",
    )

    factory = LLMProviderFactory(
        control_service=_StubControlService(),
        openai_oauth_service=_StubOauthService(status="connected", token="oauth-token"),
    )

    with patch("infrastructure.ai.provider_factory.OpenAIProvider") as mock_provider:
        factory.create_from_profile(profile)

    settings = mock_provider.call_args.args[0]
    assert settings.api_key == "oauth-token"
    assert settings.default_model == "gpt-5.4"


def test_create_from_profile_returns_mock_when_oauth_not_connected():
    profile = LLMProfile(
        id="openai-oauth",
        name="OpenAI OAuth",
        preset_key="openai-official",
        protocol="openai",
        api_key="",
        model="gpt-5.4",
        auth_mode="oauth",
    )

    factory = LLMProviderFactory(
        control_service=_StubControlService(),
        openai_oauth_service=_StubOauthService(status="disconnected", token=None),
    )

    result = factory.create_from_profile(profile)

    assert isinstance(result, MockProvider)
