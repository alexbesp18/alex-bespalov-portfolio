"""Tests for configuration management."""

from pathlib import Path

from src.config import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_settings(self):
        """Test that default settings are loaded."""
        settings = Settings()
        assert settings.config_file == "stock_options_wx_v3.jsonl"
        assert settings.log_level == "INFO"
        assert settings.log_file == "trading_scanner.log"
        assert settings.scanner_interval == 60
        assert settings.scanner_enabled is True

    def test_get_config_path(self):
        """Test getting config file path."""
        settings = Settings()
        config_path = settings.get_config_path()
        assert isinstance(config_path, Path)
        assert config_path.name == "stock_options_wx_v3.jsonl"

    def test_get_log_path(self):
        """Test getting log file path."""
        settings = Settings()
        log_path = settings.get_log_path()
        assert isinstance(log_path, Path)
        assert log_path.name == "trading_scanner.log"

