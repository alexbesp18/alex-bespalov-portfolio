"""Configuration management for options tracking application."""

from pathlib import Path
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Configuration file path
    config_file: str = "stock_options_wx_v3.jsonl"

    # Logging configuration
    log_level: str = "INFO"
    log_file: str = "trading_scanner.log"

    # Scanner configuration
    scanner_interval: int = 60  # seconds between scans
    scanner_enabled: bool = True

    # yfinance API configuration
    yfinance_timeout: int = 10  # seconds
    yfinance_retry_attempts: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    def get_config_path(self) -> Path:
        """Get absolute path to configuration file."""
        return Path(self.config_file)

    def get_log_path(self) -> Path:
        """Get absolute path to log file."""
        return Path(self.log_file)


# Global settings instance
settings = Settings()

