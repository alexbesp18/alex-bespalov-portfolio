"""
Retry Decorator with Exponential Backoff

Provides robust retry logic for unreliable operations like LLM API calls.

Example:
    >>> @retry(max_attempts=3, backoff_factor=2.0)
    ... def call_api():
    ...     response = requests.get("https://api.example.com")
    ...     response.raise_for_status()
    ...     return response.json()
"""

import functools
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple, Type, Union, Any

__all__ = ["retry", "RetryError", "RetryConfig"]

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    
    def __init__(self, message: str, last_exception: Optional[Exception] = None, attempts: int = 0):
        super().__init__(message)
        self.last_exception = last_exception
        self.attempts = attempts


@dataclass
class RetryConfig:
    """Configuration for retry behavior.
    
    Attributes:
        max_attempts: Maximum number of attempts (including initial).
        backoff_factor: Multiplier for exponential backoff (e.g., 2.0 = double each time).
        initial_delay: Initial delay in seconds before first retry.
        max_delay: Maximum delay between retries.
        jitter: Add randomness to delays to prevent thundering herd.
        exceptions: Tuple of exception types to retry on.
        on_retry: Optional callback called on each retry.
    """
    max_attempts: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.
        
        Args:
            attempt: Current attempt number (1-indexed).
            
        Returns:
            Delay in seconds.
        """
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add +/- 25% randomness
            jitter_range = delay * 0.25
            delay = delay + random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
) -> Callable:
    """Decorator that retries a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts.
        backoff_factor: Multiplier for delay between attempts.
        initial_delay: Initial delay in seconds.
        max_delay: Maximum delay between retries.
        jitter: Add randomness to delays.
        exceptions: Exception types to catch and retry.
        on_retry: Callback on each retry (exc, attempt, delay).
        
    Returns:
        Decorated function.
        
    Example:
        >>> @retry(max_attempts=3, exceptions=(ConnectionError, TimeoutError))
        ... def fetch_data():
        ...     return requests.get(url).json()
    """
    # Normalize exceptions to tuple
    if isinstance(exceptions, type) and issubclass(exceptions, Exception):
        exceptions = (exceptions,)
    
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_factor=backoff_factor,
        initial_delay=initial_delay,
        max_delay=max_delay,
        jitter=jitter,
        exceptions=exceptions,
        on_retry=on_retry,
    )
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        # Last attempt failed
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}: {e}"
                        )
                        raise RetryError(
                            f"Failed after {config.max_attempts} attempts: {e}",
                            last_exception=e,
                            attempts=attempt,
                        ) from e
                    
                    # Calculate delay and wait
                    delay = config.get_delay(attempt)
                    
                    logger.warning(
                        f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    # Call on_retry callback if provided
                    if config.on_retry:
                        try:
                            config.on_retry(e, attempt, delay)
                        except Exception as callback_err:
                            logger.warning(f"on_retry callback failed: {callback_err}")
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise RetryError(
                f"Unexpected state after {config.max_attempts} attempts",
                last_exception=last_exception,
                attempts=config.max_attempts,
            )
        
        return wrapper
    
    return decorator


# Common exception sets for convenience
NETWORK_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
)

# Rate limit exceptions (add provider-specific ones as needed)
RATE_LIMIT_EXCEPTIONS = (
    # These would be imported from provider SDKs
    # openai.RateLimitError,
    # anthropic.RateLimitError,
)


def create_llm_retry(
    max_attempts: int = 3,
    initial_delay: float = 2.0,
    on_retry: Optional[Callable] = None,
) -> Callable:
    """Create a retry decorator configured for LLM API calls.
    
    Handles common LLM API errors like rate limits and timeouts.
    
    Args:
        max_attempts: Maximum retry attempts.
        initial_delay: Initial delay (longer for LLMs due to rate limits).
        on_retry: Optional callback.
        
    Returns:
        Configured retry decorator.
    """
    return retry(
        max_attempts=max_attempts,
        backoff_factor=2.0,
        initial_delay=initial_delay,
        max_delay=60.0,
        jitter=True,
        exceptions=(
            ConnectionError,
            TimeoutError,
            OSError,
            # Add specific rate limit errors
        ),
        on_retry=on_retry,
    )

