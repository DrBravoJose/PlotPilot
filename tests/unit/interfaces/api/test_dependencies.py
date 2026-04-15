"""测试依赖注入配置"""
import os
import sys
import types
from unittest.mock import patch, MagicMock
from application.paths import DATA_DIR
from interfaces.api.dependencies import get_llm_service, get_openai_oauth_service, get_vector_store


def _fake_qdrant_module(mock_qdrant):
    module = types.ModuleType("infrastructure.ai.qdrant_vector_store")
    module.QdrantVectorStore = mock_qdrant
    return module


class TestGetVectorStore:
    """测试 get_vector_store 依赖注入函数"""

    def test_get_vector_store_returns_none_when_no_env(self):
        """未设置环境变量时返回 None"""
        with patch.dict(os.environ, {}, clear=True):
            result = get_vector_store()
            assert result is None

    def test_get_vector_store_returns_none_when_disabled(self):
        """VECTOR_STORE_ENABLED 为 false 时返回 None"""
        with patch.dict(os.environ, {"VECTOR_STORE_ENABLED": "false"}, clear=True):
            result = get_vector_store()
            assert result is None

    def test_get_vector_store_returns_qdrant_when_env_set(self):
        """设置环境变量时返回 QdrantVectorStore 实例"""
        with patch.dict(os.environ, {
            "VECTOR_STORE_ENABLED": "true",
            "VECTOR_STORE_TYPE": "qdrant",
            "QDRANT_HOST": "localhost",
            "QDRANT_PORT": "6333"
        }, clear=True):
            # Mock QdrantVectorStore to avoid actual connection
            mock_qdrant = MagicMock()
            mock_instance = MagicMock()
            mock_qdrant.return_value = mock_instance
            with patch.dict(sys.modules, {
                "infrastructure.ai.qdrant_vector_store": _fake_qdrant_module(mock_qdrant)
            }):
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
            "VECTOR_STORE_ENABLED": "true",
            "VECTOR_STORE_TYPE": "qdrant",
            "QDRANT_HOST": "qdrant.example.com",
            "QDRANT_PORT": "6334"
        }, clear=True):
            mock_qdrant = MagicMock()
            mock_instance = MagicMock()
            mock_qdrant.return_value = mock_instance
            with patch.dict(sys.modules, {
                "infrastructure.ai.qdrant_vector_store": _fake_qdrant_module(mock_qdrant)
            }):
                result = get_vector_store()

            mock_qdrant.assert_called_once_with(
                host="qdrant.example.com",
                port=6334,
                api_key=None
            )

    def test_get_vector_store_with_api_key(self):
        """使用 API key"""
        with patch.dict(os.environ, {
            "VECTOR_STORE_ENABLED": "true",
            "VECTOR_STORE_TYPE": "qdrant",
            "QDRANT_HOST": "localhost",
            "QDRANT_PORT": "6333",
            "QDRANT_API_KEY": "test-api-key"
        }, clear=True):
            mock_qdrant = MagicMock()
            mock_instance = MagicMock()
            mock_qdrant.return_value = mock_instance
            with patch.dict(sys.modules, {
                "infrastructure.ai.qdrant_vector_store": _fake_qdrant_module(mock_qdrant)
            }):
                result = get_vector_store()

            mock_qdrant.assert_called_once_with(
                host="localhost",
                port=6333,
                api_key="test-api-key"
            )

    def test_get_vector_store_uses_default_values(self):
        """只设置 qdrant 必需开关，使用默认 host/port。"""
        with patch.dict(os.environ, {
            "VECTOR_STORE_ENABLED": "true",
            "VECTOR_STORE_TYPE": "qdrant",
        }, clear=True):
            mock_qdrant = MagicMock()
            mock_instance = MagicMock()
            mock_qdrant.return_value = mock_instance
            with patch.dict(sys.modules, {
                "infrastructure.ai.qdrant_vector_store": _fake_qdrant_module(mock_qdrant)
            }):
                result = get_vector_store()

            # 验证使用默认值
            mock_qdrant.assert_called_once_with(
                host="localhost",
                port=6333,
                api_key=None
            )


def test_get_openai_oauth_service_uses_project_auth_file():
    get_openai_oauth_service.cache_clear()
    try:
        service = get_openai_oauth_service()
        assert service._auth_file == DATA_DIR / "system" / "openai_oauth.json"
    finally:
        get_openai_oauth_service.cache_clear()


def test_get_llm_service_uses_codex_provider_for_openai_oauth():
    class _StubSettingsService:
        def get_settings(self, oauth_status=None):
            return {
                "current_provider": "openai",
                "provider_settings": {
                    "openai": {
                        "selected_model": "gpt-5.4",
                        "auth_mode": "oauth",
                        "ready": True,
                    }
                },
            }

    class _StubOauthService:
        def get_status(self):
            return {"status": "connected", "message": ""}

        def get_access_token(self):
            return "jwt-token"

    fake_module = types.ModuleType("infrastructure.ai.providers.codex_provider")

    class _FakeCodexProvider:
        def __init__(self, settings, auth_file=None):
            self.settings = settings
            self.auth_file = auth_file

    fake_module.CodexProvider = _FakeCodexProvider

    with patch("interfaces.api.dependencies.get_llm_settings_service", return_value=_StubSettingsService()):
        with patch("interfaces.api.dependencies.get_openai_oauth_service", return_value=_StubOauthService()):
            with patch.dict(sys.modules, {"infrastructure.ai.providers.codex_provider": fake_module}):
                provider = get_llm_service()

    assert isinstance(provider, _FakeCodexProvider)
    assert provider.settings.api_key == "jwt-token"
    assert provider.settings.default_model == "gpt-5.4"
