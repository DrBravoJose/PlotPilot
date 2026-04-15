"""LLM provider registry used by runtime settings and frontend discovery."""

LLM_PROVIDER_REGISTRY = {
    "anthropic": {
        "label": "Claude",
        "default_model": "claude-sonnet-4-6",
        "models": ["claude-sonnet-4-6"],
        "auth_modes": [],
    },
    "openai": {
        "label": "OpenAI",
        "default_model": "gpt-5.4",
        "models": ["gpt-5.4", "gpt-4.1"],
        "auth_modes": ["api_key", "oauth"],
    },
    "minimax": {
        "label": "MiniMax",
        "default_model": "MiniMax-M2.7",
        "models": ["MiniMax-M2.7"],
        "auth_modes": [],
    },
}


def default_runtime_settings() -> dict:
    return {
        "current_provider": "anthropic",
        "provider_settings": {
            key: {
                "selected_model": value["default_model"],
                **({"auth_mode": "api_key"} if value["auth_modes"] else {}),
            }
            for key, value in LLM_PROVIDER_REGISTRY.items()
        },
    }
