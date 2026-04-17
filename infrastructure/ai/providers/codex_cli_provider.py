from __future__ import annotations

import asyncio
import hashlib
import os
import tempfile
from pathlib import Path
from typing import AsyncIterator, Callable

from domain.ai.services.llm_service import GenerationConfig, GenerationResult
from domain.ai.value_objects.prompt import Prompt
from domain.ai.value_objects.token_usage import TokenUsage
from infrastructure.ai.config.settings import Settings

from .base import BaseProvider


class CodexCLIProvider(BaseProvider):
    """通过本机 Codex CLI 调用模型，消耗 Codex 登录态对应额度。"""

    def __init__(
        self,
        settings: Settings,
        codex_bin: str = "codex",
        workspace_root: Path | None = None,
        output_path_factory: Callable[[], Path] | None = None,
    ):
        super().__init__(settings)
        self.codex_bin = codex_bin
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.output_path_factory = output_path_factory or self._default_output_path

    async def generate(self, prompt: Prompt, config: GenerationConfig) -> GenerationResult:
        output_path = self.output_path_factory()
        workspace = self._ensure_ascii_workspace(self.workspace_root)
        model = (config.model or self.settings.default_model or "").strip()
        request_prompt = self._build_request_prompt(prompt, config)

        args = [
            self.codex_bin,
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "-s",
            "read-only",
            "-C",
            str(workspace),
            "--output-last-message",
            str(output_path),
        ]
        if model:
            args.extend(["-m", model])
        args.append("-")

        process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "NO_COLOR": "1"},
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(request_prompt.encode("utf-8")),
            timeout=self.settings.timeout_seconds,
        )

        if process.returncode != 0:
            error_text = (stderr or stdout).decode("utf-8", errors="ignore").strip()
            raise RuntimeError(error_text or "Codex CLI 调用失败")

        content = output_path.read_text(encoding="utf-8").strip()
        if not content:
            raise RuntimeError("Codex CLI returned empty content")

        return GenerationResult(
            content=content,
            token_usage=TokenUsage(input_tokens=0, output_tokens=0),
        )

    async def stream_generate(self, prompt: Prompt, config: GenerationConfig) -> AsyncIterator[str]:
        result = await self.generate(prompt, config)
        yield result.content

    @staticmethod
    def _build_request_prompt(prompt: Prompt, config: GenerationConfig) -> str:
        lines = [
            "You are being used as a pure text generation engine inside PlotPilot.",
            "Do not run shell commands.",
            "Do not inspect or modify files.",
            "Return only the answer content requested by the prompt.",
            "",
            "System instructions:",
            prompt.system.strip(),
            "",
            "User request:",
            prompt.user.strip(),
        ]
        if config.response_format:
            lines.extend(["", "Response format hint:", str(config.response_format)])
        return "\n".join(lines).strip()

    @staticmethod
    def _default_output_path() -> Path:
        fd, path = tempfile.mkstemp(prefix="plotpilot-codex-", suffix=".txt")
        os.close(fd)
        return Path(path)

    @staticmethod
    def _ensure_ascii_workspace(workspace_root: Path) -> Path:
        text = str(workspace_root)
        if text.isascii():
            return workspace_root

        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
        link = Path(tempfile.gettempdir()) / f"plotpilot-codex-{digest}"
        if link.is_symlink() and link.resolve() == workspace_root.resolve():
            return link
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(workspace_root, target_is_directory=True)
        return link
