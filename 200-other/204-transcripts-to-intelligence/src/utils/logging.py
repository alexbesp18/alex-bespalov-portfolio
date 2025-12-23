"""
Structured Logging Configuration

Provides structured (JSON) logging for production use.
Can be configured for human-readable or JSON output.

Usage:
    from src.utils.logging import get_logger, configure_logging
    
    configure_logging(json_format=True)  # For production
    logger = get_logger(__name__)
    
    logger.info("processing_video", video_id="abc123", cost_usd=0.05)
"""

import logging
import os
import sys
from typing import Optional

__all__ = ["get_logger", "configure_logging", "add_context"]

# Check if structlog is available
try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


def configure_logging(
    level: int = logging.INFO,
    json_format: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """Configure logging for the application.
    
    Args:
        level: Logging level (default: INFO).
        json_format: Use JSON format (recommended for production).
        log_file: Optional file path for log output.
    """
    if STRUCTLOG_AVAILABLE and json_format:
        _configure_structlog(level, log_file)
    else:
        _configure_standard_logging(level, log_file)


def _configure_standard_logging(level: int, log_file: Optional[str]) -> None:
    """Configure standard Python logging."""
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def _configure_structlog(level: int, log_file: Optional[str]) -> None:
    """Configure structlog for JSON output."""
    # Configure standard logging for structlog to use
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )
    
    # Determine if we're in development or production
    is_development = os.environ.get("ENV", "development").lower() == "development"
    
    if is_development:
        # Human-readable output for development
        processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]
    else:
        # JSON output for production
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Get a logger instance.
    
    Returns a structlog logger if available, otherwise standard logging.
    
    Args:
        name: Logger name (usually __name__).
        
    Returns:
        Logger instance.
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


def add_context(**kwargs) -> None:
    """Add context variables to all subsequent log messages.
    
    Context persists for the current async/thread context.
    
    Args:
        **kwargs: Key-value pairs to add to context.
        
    Example:
        add_context(video_id="abc123", user_id="user1")
        logger.info("processing")  # Will include video_id and user_id
    """
    if STRUCTLOG_AVAILABLE:
        structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all context variables."""
    if STRUCTLOG_AVAILABLE:
        structlog.contextvars.clear_contextvars()


class LogContext:
    """Context manager for temporary logging context.
    
    Example:
        with LogContext(video_id="abc123"):
            logger.info("processing")  # Includes video_id
        logger.info("done")  # video_id not included
    """
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self._tokens = []
    
    def __enter__(self):
        if STRUCTLOG_AVAILABLE:
            for key, value in self.context.items():
                token = structlog.contextvars.bind_contextvars(**{key: value})
                self._tokens.append((key, token))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if STRUCTLOG_AVAILABLE:
            # Unbind all context vars we added
            structlog.contextvars.unbind_contextvars(*[k for k, _ in self._tokens])
        return False


# Convenience functions for common log patterns

def log_video_processing(
    logger,
    video_id: str,
    action: str,
    **extra,
) -> None:
    """Log video processing event with standard fields.
    
    Args:
        logger: Logger instance.
        video_id: YouTube video ID.
        action: Action being performed.
        **extra: Additional fields.
    """
    logger.info(
        action,
        video_id=video_id,
        **extra,
    )


def log_llm_call(
    logger,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    latency_seconds: float,
    **extra,
) -> None:
    """Log LLM API call with standard fields.
    
    Args:
        logger: Logger instance.
        model: Model used.
        input_tokens: Input token count.
        output_tokens: Output token count.
        cost_usd: Cost in USD.
        latency_seconds: Request latency.
        **extra: Additional fields.
    """
    logger.info(
        "llm_call",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        latency_seconds=latency_seconds,
        **extra,
    )


def log_error(
    logger,
    error: Exception,
    context: str = "",
    **extra,
) -> None:
    """Log error with standard fields.
    
    Args:
        logger: Logger instance.
        error: The exception.
        context: Context description.
        **extra: Additional fields.
    """
    logger.error(
        "error",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context,
        **extra,
    )

