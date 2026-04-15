from pathlib import Path

from application.ai.services.llm_settings_service import LlmSettingsService


def test_get_settings_returns_defaults_when_file_missing(tmp_path: Path):
    service = LlmSettingsService(settings_file=tmp_path / "llm_settings.json")

    settings = service.get_settings()

    assert settings["current_provider"] == "anthropic"
    assert settings["provider_settings"]["minimax"]["selected_model"] == "MiniMax-M2.7"


def test_update_settings_persists_partial_changes(tmp_path: Path):
    service = LlmSettingsService(settings_file=tmp_path / "llm_settings.json")

    updated = service.update_settings(
        {
            "current_provider": "openai",
            "provider_settings": {
                "openai": {"selected_model": "gpt-5.4", "auth_mode": "oauth"}
            },
        }
    )

    assert updated["current_provider"] == "openai"
    assert updated["provider_settings"]["openai"]["auth_mode"] == "oauth"
    assert (tmp_path / "llm_settings.json").exists()


def test_compute_readiness_marks_openai_oauth_unready_without_token(tmp_path: Path):
    service = LlmSettingsService(settings_file=tmp_path / "llm_settings.json")
    service.update_settings(
        {"provider_settings": {"openai": {"auth_mode": "oauth"}}}
    )

    state = service.get_settings(oauth_status={"status": "disconnected"})

    assert state["provider_settings"]["openai"]["ready"] is False


def test_get_settings_normalizes_legacy_minimax_model_and_marks_missing_key_unready(tmp_path: Path):
    settings_file = tmp_path / "llm_settings.json"
    settings_file.write_text(
        '{"current_provider":"minimax","provider_settings":{"minimax":{"selected_model":"MiniMax-M2.5"}}}',
        encoding="utf-8",
    )
    service = LlmSettingsService(settings_file=settings_file)

    settings = service.get_settings()

    assert settings["provider_settings"]["minimax"]["selected_model"] == "MiniMax-M2.7"
    assert settings["provider_settings"]["minimax"]["ready"] is False
