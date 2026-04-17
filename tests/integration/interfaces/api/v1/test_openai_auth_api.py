from fastapi import FastAPI
from fastapi.testclient import TestClient

from interfaces.api.dependencies import get_openai_oauth_service
from interfaces.api.v1.system.openai_auth_routes import router


class _StubOauthService:
    def get_status(self):
        return {"status": "disconnected", "message": ""}

    def start_auth_flow(self):
        return {"status": "pending", "message": "已发起 Codex OAuth 登录"}

    def logout(self):
        return {"status": "disconnected", "message": "Logged out"}


def test_get_openai_auth_status_returns_disconnected():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_openai_oauth_service] = lambda: _StubOauthService()
    client = TestClient(app)

    try:
        response = client.get("/api/v1/auth/openai/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] in {"disconnected", "connected", "pending", "error"}


def test_start_openai_auth_returns_pending_status():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_openai_oauth_service] = lambda: _StubOauthService()
    client = TestClient(app)

    try:
        response = client.post("/api/v1/auth/openai/start")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "pending",
        "message": "已发起 Codex OAuth 登录",
    }
