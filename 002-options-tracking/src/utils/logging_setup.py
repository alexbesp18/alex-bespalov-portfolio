"""Centralized logging configuration."""

import logging
from pathlib import Path
from typing import Optional

from src.config import settings


def setup_logging(log_file: Optional[str] = None, log_level: Optional[str] = None) -> logging.Logger:
    """Set up logging configuration.

    Args:
        log_file: Path to log file. If None, uses settings.log_file.
        log_level: Logging level. If None, uses settings.log_level.

    Returns:
        Configured logger instance.
    """
    log_file = log_file or settings.log_file
    log_level = log_level or settings.log_level

    # Create log directory if it doesn't exist
    log_path = Path(log_file)
    if log_path.parent != Path("."):
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create console and file handlers
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")

    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure root logger
    logger = logging.getLogger("trading_scanner")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent duplicate logs
    logger.propagate = False

    # Create specialized loggers
    console_logger = logging.getLogger("trading_scanner.console")
    console_logger.setLevel(logging.INFO)
    console_logger.addHandler(console_handler)
    console_logger.propagate = False

    file_logger = logging.getLogger("trading_scanner.file")
    file_logger.setLevel(logging.WARNING)
    file_logger.addHandler(file_handler)
    file_logger.propagate = False

    return logger


def get_logger(name: str = "trading_scanner") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)

