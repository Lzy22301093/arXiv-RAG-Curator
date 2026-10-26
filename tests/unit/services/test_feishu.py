from unittest.mock import MagicMock, patch

from src.config import FeishuSettings
from src.services.feishu.bot import FeishuBot
from src.services.feishu.factory import make_feishu_service


class TestFeishuBot:
    """Test Feishu bot."""

    def test_bot_creation(self):
        """Test creating bot instance."""
        bot = FeishuBot(
            app_id="test_app_id",
            app_secret="test_app_secret",
            verification_token="test_token",
            encrypt_key="test_key",
            opensearch_client=MagicMock(),
            embeddings_client=MagicMock(),
            llm_client=MagicMock(),
        )

        assert bot.app_id == "test_app_id"
        assert bot.app_secret == "test_app_secret"
        assert bot.verification_token == "test_token"
        assert bot.encrypt_key == "test_key"
        assert bot.opensearch is not None
        assert bot.embeddings is not None
        assert bot.llm is not None

    def test_bot_creation_with_cache(self):
        """Test creating bot instance with cache client."""
        cache_mock = MagicMock()
        bot = FeishuBot(
            app_id="test_app_id",
            app_secret="test_app_secret",
            verification_token="test_token",
            encrypt_key="",
            opensearch_client=MagicMock(),
            embeddings_client=MagicMock(),
            llm_client=MagicMock(),
            cache_client=cache_mock,
        )

        assert bot.cache is cache_mock


class TestFeishuSettings:
    """Test Feishu settings."""

    def test_default_settings(self):
        """Test default settings."""
        settings = FeishuSettings(app_id="", app_secret="", verification_token="", encrypt_key="", enabled=False)
        assert settings.enabled is False
        assert settings.app_id == ""
        assert settings.app_secret == ""
        assert settings.verification_token == ""
        assert settings.encrypt_key == ""

    def test_custom_settings(self):
        """Test custom settings."""
        settings = FeishuSettings(
            app_id="cli_test",
            app_secret="secret",
            verification_token="token",
            encrypt_key="key",
            enabled=True,
        )
        assert settings.enabled is True
        assert settings.app_id == "cli_test"
        assert settings.app_secret == "secret"
        assert settings.verification_token == "token"
        assert settings.encrypt_key == "key"


class TestFeishuFactory:
    """Test factory."""

    @patch("src.services.feishu.factory.get_settings")
    def test_factory_disabled(self, mock_settings):
        """Test factory returns None when disabled."""
        mock_settings.return_value.feishu.enabled = False
        bot = make_feishu_service(
            opensearch_client=MagicMock(),
            embeddings_client=MagicMock(),
            llm_client=MagicMock(),
        )
        assert bot is None

    @patch("src.services.feishu.factory.get_settings")
    def test_factory_no_credentials(self, mock_settings):
        """Test factory returns None without credentials."""
        mock_settings.return_value.feishu.enabled = True
        mock_settings.return_value.feishu.app_id = ""
        mock_settings.return_value.feishu.app_secret = ""
        bot = make_feishu_service(
            opensearch_client=MagicMock(),
            embeddings_client=MagicMock(),
            llm_client=MagicMock(),
        )
        assert bot is None

    @patch("src.services.feishu.factory.get_settings")
    def test_factory_success(self, mock_settings):
        """Test factory creates bot."""
        mock_settings.return_value.feishu.enabled = True
        mock_settings.return_value.feishu.app_id = "cli_test"
        mock_settings.return_value.feishu.app_secret = "secret"
        mock_settings.return_value.feishu.verification_token = "token"
        mock_settings.return_value.feishu.encrypt_key = ""
        bot = make_feishu_service(
            opensearch_client=MagicMock(),
            embeddings_client=MagicMock(),
            llm_client=MagicMock(),
        )
        assert bot is not None
        assert bot.app_id == "cli_test"
        assert bot.app_secret == "secret"
