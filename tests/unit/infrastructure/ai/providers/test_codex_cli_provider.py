from pathlib import Path
from types import SimpleNamespace

import pytest

from domain.ai.services.llm_service import GenerationConfig
from domain.ai.value_objects.prompt import Prompt
from infrastructure.ai.config.settings import Settings
from infrastructure.ai.providers.codex_cli_provider import CodexCLIProvider


class _FakeProcess:
    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    async def communicate(self, input=None):
        return self._stdout, self._stderr


@pytest.mark.anyio
async def test_generate_reads_output_last_message_file(tmp_path, monkeypatch):
    output_file = tmp_path / "last-message.txt"
    output_file.write_text("Codex answer", encoding="utf-8")
    captured = {}

    async def fake_exec(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return _FakeProcess()

    provider = CodexCLIProvider(
        Settings(default_model="gpt-5.4"),
        workspace_root=tmp_path,
        output_path_factory=lambda: output_file,
    )

    monkeypatch.setattr(
        "infrastructure.ai.providers.codex_cli_provider.asyncio.create_subprocess_exec",
        fake_exec,
    )

    result = await provider.generate(
        Prompt(system="system", user="user"),
        GenerationConfig(model="gpt-5.4"),
    )

    assert result.content == "Codex answer"
    assert "codex" in captured["args"][0]
    assert "--output-last-message" in captured["args"]
    assert captured["kwargs"]["stdin"] is not None


@pytest.mark.anyio
async def test_generate_raises_when_codex_command_fails(tmp_path, monkeypatch):
    output_file = tmp_path / "last-message.txt"

    async def fake_exec(*args, **kwargs):
        return _FakeProcess(returncode=1, stderr=b"Not logged in")

    provider = CodexCLIProvider(
        Settings(default_model="gpt-5.4"),
        workspace_root=tmp_path,
        output_path_factory=lambda: output_file,
    )

    monkeypatch.setattr(
        "infrastructure.ai.providers.codex_cli_provider.asyncio.create_subprocess_exec",
        fake_exec,
    )

    with pytest.raises(RuntimeError, match="Not logged in"):
        await provider.generate(
            Prompt(system="system", user="user"),
            GenerationConfig(model="gpt-5.4"),
        )
