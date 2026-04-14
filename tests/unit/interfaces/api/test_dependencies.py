"""测试依赖注入配置"""
import os
import sys
import types
from unittest.mock import MagicMock, patch

anthropic_stub = types.ModuleType("anthropic")
anthropic_stub.Anthropic = object
anthropic_stub.AsyncAnthropic = object
sys.modules.setdefault("anthropic", anthropic_stub)

from interfaces.api.dependencies import get_llm_service, get_vector_store
from infrastructure.ai.providers.mock_provider import MockProvider


class TestGetVectorStore:
    """测试 get_vector_store 依赖注入函数"""

    def test_get_vector_store_returns_none_when_no_env(self):
        """未设置环境变量时返回 None"""
        with patch.dict(os.environ, {}, clear=True):
            result = get_vector_store()
            assert result is None

    def test_get_vector_store_returns_none_when_disabled(self):
        """QDRANT_ENABLED 为 false 时返回 None"""
        with patch.dict(os.environ, {"QDRANT_ENABLED": "false"}, clear=True):
            result = get_vector_store()
            assert result is None

    def test_get_vector_store_returns_qdrant_when_env_set(self):
        """设置环境变量时返回 QdrantVectorStore 实例"""
        with patch.dict(os.environ, {
            "QDRANT_ENABLED": "true",
            "QDRANT_HOST": "localhost",
            "QDRANT_PORT": "6333"
        }, clear=True):
            # Mock QdrantVectorStore to avoid actual connection
            with patch("infrastructure.ai.qdrant_vector_store.QdrantVectorStore") as mock_qdrant:
                mock_instance = MagicMock()
                mock_qdrant.return_value = mock_instance

                result = get_vector_store()

                # 验证返回了实例
                assert result is mock_instance
                # 验证使用正确的参数初始化
                mock_qdrant.assert_called_once_with(
                    host="localhost",
                    port=6333,
                    api_key=None
                )

    def test_get_vector_store_with_custom_host_port(self):
        """使用自定义 host 和 port"""
        with patch.dict(os.environ, {
            "QDRANT_ENABLED": "true",
            "QDRANT_HOST": "qdrant.example.com",
            "QDRANT_PORT": "6334"
        }, clear=True):
            with patch("infrastructure.ai.qdrant_vector_store.QdrantVectorStore") as mock_qdrant:
                mock_instance = MagicMock()
                mock_qdrant.return_value = mock_instance

                result = get_vector_store()

                mock_qdrant.assert_called_once_with(
                    host="qdrant.example.com",
                    port=6334,
                    api_key=None
                )

    def test_get_vector_store_with_api_key(self):
        """使用 API key"""
        with patch.dict(os.environ, {
            "QDRANT_ENABLED": "true",
            "QDRANT_HOST": "localhost",
            "QDRANT_PORT": "6333",
            "QDRANT_API_KEY": "test-api-key"
        }, clear=True):
            with patch("infrastructure.ai.qdrant_vector_store.QdrantVectorStore") as mock_qdrant:
                mock_instance = MagicMock()
                mock_qdrant.return_value = mock_instance

                result = get_vector_store()

                mock_qdrant.assert_called_once_with(
                    host="localhost",
                    port=6333,
                    api_key="test-api-key"
                )

    def test_get_vector_store_uses_default_values(self):
        """只设置 QDRANT_ENABLED，使用默认值"""
        with patch.dict(os.environ, {
            "QDRANT_ENABLED": "true"
        }, clear=True):
            with patch("infrastructure.ai.qdrant_vector_store.QdrantVectorStore") as mock_qdrant:
                mock_instance = MagicMock()
                mock_qdrant.return_value = mock_instance

                result = get_vector_store()

                # 验证使用默认值
                mock_qdrant.assert_called_once_with(
                    host="localhost",
                    port=6333,
                    api_key=None
                )


class TestGetLlmService:
    """测试 get_llm_service 依赖注入函数"""

    def test_get_llm_service_returns_openai_provider_for_minimax(self):
        """LLM_PROVIDER=minimax 时走 OpenAI 兼容 provider。"""
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "minimax",
                "MINIMAX_API_KEY": "test-minimax-key",
            },
            clear=True,
        ):
            with patch(
                "infrastructure.ai.providers.openai_provider.OpenAIProvider"
            ) as mock_openai_provider:
                mock_instance = MagicMock()
                mock_openai_provider.return_value = mock_instance

                result = get_llm_service()

                assert result is mock_instance
                mock_openai_provider.assert_called_once()
                settings = mock_openai_provider.call_args.args[0]
                assert settings.api_key == "test-minimax-key"
                assert settings.base_url == "https://api.minimaxi.com/v1"

    def test_get_llm_service_returns_mock_for_minimax_without_key(self):
        """LLM_PROVIDER=minimax 但未配置 key 时回退 MockProvider。"""
        with patch.dict(os.environ, {"LLM_PROVIDER": "minimax"}, clear=True):
            result = get_llm_service()
            assert isinstance(result, MockProvider)

    def test_get_llm_service_returns_anthropic_provider_when_configured(self):
        """Anthropic 现有分支保持不变。"""
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
            },
            clear=True,
        ):
            with patch(
                "infrastructure.ai.providers.anthropic_provider.AnthropicProvider"
            ) as mock_anthropic:
                mock_instance = MagicMock()
                mock_anthropic.return_value = mock_instance

                result = get_llm_service()

                assert result is mock_instance
                mock_anthropic.assert_called_once()
