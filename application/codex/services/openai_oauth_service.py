from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any


class OpenAiOauthService:
    """兼容旧接口名，实际委托给本机 Codex CLI 登录态。"""

    _AUTH_URL_RE = re.compile(r"https://auth\.openai\.com/oauth/authorize\?[^\s]+")
    _DEFAULT_MODELS = [
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.2",
        "gpt-5.2-codex",
        "gpt-5.2-codex-max",
        "gpt-5.1-codex-mini",
    ]

    def __init__(
        self,
        codex_bin: str = "codex",
        login_log: Path | None = None,
    ):
        self._codex_bin = codex_bin
        self._login_log = login_log or (Path.home() / ".codex" / "log" / "codex-login.log")

    def get_status(self) -> dict[str, Any]:
        result = self._run([self._codex_bin, "login", "status"], check=False)
        output = (result.stdout or result.stderr or "").strip()

        if result.returncode == 0:
          return {"status": "connected", "message": output or "Codex 已登录"}
        if "Not logged in" in output:
          return {"status": "disconnected", "message": "Codex 未登录"}
        return {"status": "error", "message": output or "Codex 登录状态未知"}

    def get_access_token(self) -> str | None:
        # Codex CLI 不暴露可复用的 API access token；调用链改为直接 shell 到 `codex exec`。
        return None

    def list_models(self) -> list[dict[str, str]]:
        return [
            {"id": model, "name": model, "owned_by": "codex"}
            for model in self._DEFAULT_MODELS
        ]

    def start_auth_flow(self) -> dict[str, Any]:
        status = self.get_status()
        if status["status"] == "connected":
            return status

        login_url = self._start_detached_login()
        payload = {
            "status": "pending",
            "message": "已发起 Codex OAuth 登录，请在浏览器中完成授权",
        }
        if login_url:
            payload["url"] = login_url
        return payload

    def logout(self) -> dict[str, Any]:
        result = self._run([self._codex_bin, "logout"], check=False)
        output = (result.stdout or result.stderr or "").strip()
        if result.returncode != 0 and "Not logged in" not in output:
            return {"status": "error", "message": output or "Codex 退出登录失败"}
        return {"status": "disconnected", "message": "Codex 已退出登录"}

    def _run(self, args: list[str], check: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=check,
            env={**os.environ, "NO_COLOR": "1"},
        )

    def _start_detached_login(self) -> str | None:
        self._login_log.parent.mkdir(parents=True, exist_ok=True)
        start_offset = self._login_log.stat().st_size if self._login_log.exists() else 0
        with self._login_log.open("a", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                [self._codex_bin, "login"],
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=log_file,
                start_new_session=True,
                env={**os.environ, "NO_COLOR": "1"},
            )

        time.sleep(0.2)
        code = process.poll()
        if code not in (None, 0):
            raise RuntimeError(self._read_login_error())
        return self._wait_for_auth_url(start_offset)

    def _read_login_error(self) -> str:
        if not self._login_log.exists():
            return "Codex 登录启动失败"
        lines = self._login_log.read_text(encoding="utf-8", errors="ignore").splitlines()
        return lines[-1] if lines else "Codex 登录启动失败"

    def _wait_for_auth_url(self, start_offset: int) -> str | None:
        deadline = time.time() + 5
        while time.time() < deadline:
            if self._login_log.exists():
                with self._login_log.open("r", encoding="utf-8", errors="ignore") as handle:
                    handle.seek(start_offset)
                    match = self._AUTH_URL_RE.search(handle.read())
                if match:
                    return match.group(0)
            time.sleep(0.1)
        return None
