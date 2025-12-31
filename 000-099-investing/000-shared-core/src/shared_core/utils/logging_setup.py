"""
Logging configuration utilities.

Provides consistent logging setup across all investing projects.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    name: str = "INVESTING",
    verbose: bool = False,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.

    Args:
        name: Logger name (appears in log output)
        verbose: If True, set level to DEBUG; otherwise INFO
        log_file: Optional path to log file (in addition to console)
        format_string: Custom format string. Defaults to timestamped format.

    Returns:
        Configured logger instance.

    Example:
        >>> logger = setup_logging("ALERTS", verbose=True)
        >>> logger.info("Starting scan...")
    """
    level = logging.DEBUG if verbose else logging.INFO

    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Create formatter
    formatter = logging.Formatter(format_string, datefmt='%Y-%m-%d %H:%M:%S')

    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger by name.

    Args:
        name: Logger name

    Returns:
        Logger instance (may need setup_logging called first for formatting)
    """
    return logging.getLogger(name)

