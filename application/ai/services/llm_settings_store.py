import json
from pathlib import Path


class LlmSettingsStore:
    def __init__(self, settings_file: Path):
        self._settings_file = settings_file

    def load(self) -> dict | None:
        if not self._settings_file.exists():
            return None
        return json.loads(self._settings_file.read_text(encoding="utf-8"))

    def save(self, payload: dict) -> dict:
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)
        self._settings_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return payload
