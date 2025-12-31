"""
Configuration management for Stock Tracker application.

Centralizes all configuration settings, environment variable loading,
and logging setup.
"""
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Logging
    log_level: str = "INFO"

    # API Configuration
    twelve_data_api_key: str = ""  # Set via TWELVE_DATA_API_KEY env var
    
    # API Rate Limiting
    api_delay_seconds: float = 0.5

    # Retry Configuration
    max_retry_attempts: int = 3
    retry_base_delay: int = 1
    retry_max_delay: int = 60

    # Application Settings
    default_duration: str = "1 year"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure application-wide logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, uses value from settings.

    Returns:
        Configured logger instance.
    """
    if log_level is None:
        log_level = settings.log_level.upper()

    # Convert string to logging level constant
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Configure logging format
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {log_level} level")
    return logger


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to project root directory.
    """
    # This file is in src/, so go up one level
    return Path(__file__).parent.parent


def get_config_path() -> Path:
    """
    Get the path to the config directory.

    Returns:
        Path to config directory.
    """
    return get_project_root() / "config"


def get_stocks_config_path() -> Path:
    """
    Get the path to stocks.json configuration file.

    Returns:
        Path to stocks.json file.
    """
    return get_config_path() / "stocks.json"


# Load environment variables from .env file if it exists
env_path = get_project_root() / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Create global settings instance
settings = Settings()

# Setup logging
logger = setup_logging()

