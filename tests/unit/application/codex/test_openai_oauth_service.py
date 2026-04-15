import json
from urllib.parse import parse_qs, urlparse

from application.codex.services.openai_oauth_service import OpenAiOauthService


def test_get_status_returns_disconnected_when_auth_file_missing(tmp_path):
    service = OpenAiOauthService(auth_file=tmp_path / "auth.json")

    assert service.get_status()["status"] == "disconnected"


def test_get_access_token_reads_token_from_auth_file(tmp_path):
    auth_file = tmp_path / "auth.json"
    auth_file.write_text(
        json.dumps({"tokens": {"access_token": "test-token"}}),
        encoding="utf-8",
    )
    service = OpenAiOauthService(auth_file=auth_file)

    assert service.get_access_token() == "test-token"


def test_start_auth_flow_returns_connected_when_token_already_exists(tmp_path):
    auth_file = tmp_path / "auth.json"
    auth_file.write_text(
        json.dumps({"tokens": {"access_token": "test-token"}}),
        encoding="utf-8",
    )
    service = OpenAiOauthService(auth_file=auth_file)

    result = service.start_auth_flow()

    assert result == {"status": "connected", "message": "Already logged in"}


def test_start_auth_flow_sets_pending_status(tmp_path, monkeypatch):
    service = OpenAiOauthService(auth_file=tmp_path / "auth.json")
    monkeypatch.setattr(service, "_ensure_server", lambda: None)

    result = service.start_auth_flow()

    assert result["status"] == "pending"
    assert result["url"].startswith(service.AUTH_URL)
    params = parse_qs(urlparse(result["url"]).query)
    assert params["codex_cli_simplified_flow"] == ["true"]
    assert params["originator"] == ["codex_cli_rs"]
    assert params["id_token_add_organizations"] == ["true"]
    assert service.get_status()["status"] == "pending"


def test_build_callback_page_notifies_opener_and_closes_window(tmp_path):
    service = OpenAiOauthService(auth_file=tmp_path / "auth.json")

    html = service._build_callback_page("connected", "Login successful")

    assert "openai-oauth-complete" in html
    assert "window.close()" in html
    assert "Login successful" in html
