"""Infrastructure AI module"""
from .config import Settings
from .providers import BaseProvider
from .openai_embedding_service import OpenAIEmbeddingService

__all__ = ["Settings", "BaseProvider", "OpenAIEmbeddingService"]

try:
    from .providers import AnthropicProvider
except ImportError:  # pragma: no cover - optional provider dependency
    AnthropicProvider = None
else:
    __all__.append("AnthropicProvider")
