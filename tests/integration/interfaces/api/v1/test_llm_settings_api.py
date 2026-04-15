from fastapi import FastAPI
from fastapi.testclient import TestClient

from interfaces.api.dependencies import get_llm_settings_service, get_openai_oauth_service
from interfaces.api.v1.system.llm_settings_routes import router


class _StubSettingsService:
    def __init__(self):
        self.state = {
            "current_provider": "anthropic",
            "provider_settings": {
                "anthropic": {"selected_model": "claude-sonnet-4-6", "ready": True},
                "openai": {"selected_model": "gpt-5.4", "auth_mode": "api_key", "ready": True},
                "minimax": {"selected_model": "MiniMax-M2.7", "ready": False},
            },
        }

    def get_registry(self):
        return {"providers": []}

    def get_settings(self, oauth_status=None):
        return self.state

    def update_settings(self, payload):
        if "current_provider" in payload:
            self.state["current_provider"] = payload["current_provider"]
        for provider, provider_patch in payload.get("provider_settings", {}).items():
            self.state["provider_settings"].setdefault(provider, {})
            self.state["provider_settings"][provider].update(provider_patch)
        return self.state


class _StubOauthService:
    def get_status(self):
        return {"status": "disconnected", "message": ""}


def test_put_llm_settings_updates_current_provider():
    settings_service = _StubSettingsService()
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_llm_settings_service] = lambda: settings_service
    app.dependency_overrides[get_openai_oauth_service] = lambda: _StubOauthService()
    client = TestClient(app)

    try:
        response = client.put(
            "/api/v1/settings/llm",
            json={
                "current_provider": "minimax",
                "provider_settings": {"minimax": {"selected_model": "MiniMax-M2.7"}},
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["current_provider"] == "minimax"
