"""Infrastructure AI providers module"""
from .base import BaseProvider
from .openai_provider import OpenAIProvider

__all__ = ["BaseProvider", "OpenAIProvider"]

try:
    from .anthropic_provider import AnthropicProvider
except ModuleNotFoundError:  # pragma: no cover - optional provider dependency
    AnthropicProvider = None
else:
    __all__.append("AnthropicProvider")
