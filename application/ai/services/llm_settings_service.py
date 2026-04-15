from copy import deepcopy
import os
from pathlib import Path

from application.ai.llm_registry import LLM_PROVIDER_REGISTRY, default_runtime_settings
from application.ai.services.llm_settings_store import LlmSettingsStore
from application.paths import DATA_DIR


class LlmSettingsService:
    def __init__(self, settings_file: Path | None = None):
        self._store = LlmSettingsStore(settings_file or (DATA_DIR / "system" / "llm_settings.json"))

    def get_registry(self) -> dict:
        return {"providers": [{"key": key, **value} for key, value in LLM_PROVIDER_REGISTRY.items()]}

    def get_settings(self, oauth_status: dict | None = None) -> dict:
        state = deepcopy(default_runtime_settings())
        stored = self._store.load()
        if stored:
            state = self._merge(state, stored)
        state = self._normalize(state)
        return self._with_readiness(state, oauth_status or {"status": "disconnected"})

    def update_settings(self, payload: dict) -> dict:
        state = self.get_settings()
        merged = self._normalize(self._merge(state, payload))
        return self._store.save(
            {
                "current_provider": merged["current_provider"],
                "provider_settings": {
                    key: {field: value for field, value in provider.items() if field != "ready"}
                    for key, provider in merged["provider_settings"].items()
                },
            }
        )

    def _merge(self, base: dict, patch: dict) -> dict:
        out = deepcopy(base)
        if "current_provider" in patch:
            out["current_provider"] = patch["current_provider"]
        for provider, provider_patch in patch.get("provider_settings", {}).items():
            out["provider_settings"].setdefault(provider, {})
            out["provider_settings"][provider].update(provider_patch)
        return out

    def _normalize(self, settings: dict) -> dict:
        normalized = deepcopy(settings)

        if normalized.get("current_provider") not in LLM_PROVIDER_REGISTRY:
            normalized["current_provider"] = "anthropic"

        for provider, meta in LLM_PROVIDER_REGISTRY.items():
            provider_state = normalized["provider_settings"].setdefault(provider, {})
            if provider_state.get("selected_model") not in meta["models"]:
                provider_state["selected_model"] = meta["default_model"]

            auth_modes = meta.get("auth_modes", [])
            if auth_modes:
                if provider_state.get("auth_mode") not in auth_modes:
                    provider_state["auth_mode"] = auth_modes[0]
            else:
                provider_state.pop("auth_mode", None)

        return normalized

    def _with_readiness(self, settings: dict, oauth_status: dict) -> dict:
        for provider, provider_state in settings["provider_settings"].items():
            if provider == "openai":
                if provider_state.get("auth_mode") == "oauth":
                    provider_state["ready"] = oauth_status.get("status") == "connected"
                else:
                    provider_state["ready"] = self._has_env("OPENAI_API_KEY")
                continue

            if provider == "anthropic":
                provider_state["ready"] = self._has_env("ANTHROPIC_API_KEY")
                continue

            if provider == "minimax":
                provider_state["ready"] = self._has_env("MINIMAX_API_KEY")
                continue

            provider_state["ready"] = True
        return settings

    def _has_env(self, name: str) -> bool:
        raw = os.getenv(name)
        return bool(raw and raw.strip())
