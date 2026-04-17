from fastapi import FastAPI
from fastapi.testclient import TestClient

from interfaces.api.dependencies import get_openai_oauth_service
from application.ai.llm_control_service import LLMProfile
from interfaces.api.v1.workbench import llm_control
from interfaces.api.v1.workbench.llm_control import router


class _StubOauthService:
    def get_status(self):
        return {"status": "connected", "message": "Codex 已登录"}

    def list_models(self):
        return [
            {"id": "gpt-5.4", "name": "gpt-5.4", "owned_by": "codex"},
            {"id": "gpt-5.4-mini", "name": "gpt-5.4-mini", "owned_by": "codex"},
        ]


def test_list_models_returns_codex_models_for_oauth_profile(monkeypatch):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_openai_oauth_service] = lambda: _StubOauthService()
    monkeypatch.setattr(llm_control._service, "get_active_profile", lambda: None)
    client = TestClient(app)

    try:
        response = client.post(
            "/api/v1/llm-control/models",
            json={
                "protocol": "openai",
                "auth_mode": "oauth",
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "items": [
            {"id": "gpt-5.4", "name": "gpt-5.4", "owned_by": "codex"},
            {"id": "gpt-5.4-mini", "name": "gpt-5.4-mini", "owned_by": "codex"},
        ],
        "count": 2,
    }


def test_list_models_keeps_oauth_route_even_if_active_profile_has_api_key(monkeypatch):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_openai_oauth_service] = lambda: _StubOauthService()
    monkeypatch.setattr(
        llm_control._service,
        "get_active_profile",
        lambda: LLMProfile(
            id="active",
            name="Active profile",
            preset_key="custom-openai-compatible",
            protocol="openai",
            base_url="https://api.openai.com/v1",
            api_key="should-not-be-used",
            auth_mode="api_key",
            model="gpt-4o",
        ),
    )
    client = TestClient(app)

    try:
        response = client.post(
            "/api/v1/llm-control/models",
            json={
                "protocol": "openai",
                "auth_mode": "oauth",
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"] == [
        {"id": "gpt-5.4", "name": "gpt-5.4", "owned_by": "codex"},
        {"id": "gpt-5.4-mini", "name": "gpt-5.4-mini", "owned_by": "codex"},
    ]
