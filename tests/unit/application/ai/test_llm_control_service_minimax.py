from application.ai.llm_control_service import LLMControlService


def test_get_presets_includes_minimax_with_2_7_defaults():
    service = LLMControlService()

    presets = {preset.key: preset for preset in service.get_presets()}

    assert "minimax" in presets
    assert presets["minimax"].protocol == "minimax"
    assert presets["minimax"].default_base_url == "https://api.minimaxi.com/v1"
    assert presets["minimax"].default_model == "MiniMax-M2.7"
