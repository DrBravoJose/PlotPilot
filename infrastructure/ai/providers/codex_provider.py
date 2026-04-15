"""Codex OAuth provider backed by ChatGPT Codex backend responses API."""
import base64
import json
import logging
from pathlib import Path
from typing import AsyncIterator

import httpx

from domain.ai.services.llm_service import GenerationConfig, GenerationResult
from domain.ai.value_objects.prompt import Prompt
from domain.ai.value_objects.token_usage import TokenUsage
from infrastructure.ai.config.settings import Settings
from .base import BaseProvider

logger = logging.getLogger(__name__)

CODEX_BASE_URL = "https://chatgpt.com/backend-api"
CODEX_RESPONSES_PATH = "/codex/responses"
CODEX_DEFAULT_MODEL = "gpt-5.4"


def _decode_auth_claim(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload = parts[1]
        payload_padded = payload + "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload_padded).decode("utf-8")
        payload_json = json.loads(decoded)
        return payload_json.get("https://api.openai.com/auth", {})
    except Exception:
        return {}


def _messages_to_input(prompt: Prompt) -> tuple[str, list[dict]]:
    return (
        prompt.system or "",
        [
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": prompt.user}],
            }
        ],
    )


def _parse_sse_text(raw: str) -> str:
    parts: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("data: "):
            continue
        payload = line[6:]
        if payload == "[DONE]":
            break
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type", "")
        if event_type == "response.output_text.delta":
            delta = event.get("delta", "")
            if delta:
                parts.append(delta)
            continue

        if event_type == "response.content_part.delta":
            delta = event.get("delta", {})
            if isinstance(delta, dict):
                text = delta.get("text", "")
                if text:
                    parts.append(text)
            elif isinstance(delta, str) and delta:
                parts.append(delta)
    return "".join(parts)


class CodexProvider(BaseProvider):
    def __init__(self, settings: Settings, auth_file: Path | None = None):
        super().__init__(settings)
        if not settings.api_key:
            raise ValueError("OAuth access token is required for CodexProvider")
        self._auth_file = auth_file
        self._token = settings.api_key

    def _resolved_model(self, config: GenerationConfig) -> str:
        model = config.model or self.settings.default_model or CODEX_DEFAULT_MODEL
        if model.startswith("gpt-5") or "codex" in model:
            return model
        return CODEX_DEFAULT_MODEL

    def _load_auth_context(self) -> tuple[str, str]:
        token = self._token
        account_id = _decode_auth_claim(token).get("chatgpt_account_id", "")

        if self._auth_file and self._auth_file.exists():
            try:
                payload = json.loads(self._auth_file.read_text(encoding="utf-8"))
                stored_token = payload.get("tokens", {}).get("access_token")
                if stored_token:
                    token = stored_token
                    account_id = payload.get("chatgpt_account_id") or _decode_auth_claim(token).get(
                        "chatgpt_account_id", ""
                    )
            except json.JSONDecodeError:
                logger.warning("Failed to parse Codex auth file: %s", self._auth_file)

        if not account_id:
            raise RuntimeError("Codex OAuth token missing chatgpt_account_id")

        return token, account_id

    def _headers(self) -> dict:
        token, account_id = self._load_auth_context()
        return {
            "Authorization": f"Bearer {token}",
            "chatgpt-account-id": account_id,
            "originator": "codex_cli_rs",
            "Content-Type": "application/json",
            "accept": "text/event-stream",
        }

    def _body(self, prompt: Prompt, config: GenerationConfig) -> dict:
        instructions, input_items = _messages_to_input(prompt)
        return {
            "model": self._resolved_model(config),
            "instructions": instructions,
            "input": input_items,
            "store": False,
            # Codex backend rejects non-streaming requests, so collect SSE for sync use-cases.
            "stream": True,
        }

    async def generate(self, prompt: Prompt, config: GenerationConfig) -> GenerationResult:
        url = f"{CODEX_BASE_URL}{CODEX_RESPONSES_PATH}"
        collected = ""
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=self._body(prompt, config), headers=self._headers()) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_text():
                    collected += chunk

        content = _parse_sse_text(collected).strip()
        if not content:
            raise RuntimeError("Codex backend returned empty content")
        return GenerationResult(content=content, token_usage=TokenUsage(input_tokens=0, output_tokens=0))

    async def stream_generate(self, prompt: Prompt, config: GenerationConfig) -> AsyncIterator[str]:
        url = f"{CODEX_BASE_URL}{CODEX_RESPONSES_PATH}"
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", url, json=self._body(prompt, config), headers=self._headers()) as resp:
                resp.raise_for_status()
                buffer = ""
                async for chunk in resp.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if payload == "[DONE]":
                            return
                        try:
                            event = json.loads(payload)
                        except json.JSONDecodeError:
                            continue

                        event_type = event.get("type", "")
                        if event_type == "response.output_text.delta":
                            delta = event.get("delta", "")
                            if delta:
                                yield delta
                            continue

                        if event_type == "response.content_part.delta":
                            delta = event.get("delta", {})
                            if isinstance(delta, dict):
                                text = delta.get("text", "")
                                if text:
                                    yield text
                            elif isinstance(delta, str) and delta:
                                yield delta
