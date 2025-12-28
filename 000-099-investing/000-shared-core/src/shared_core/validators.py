"""
Input validation utilities for shared_core.

Provides validation functions for common inputs like ticker symbols,
dates, and API keys. Raises ValueError with descriptive messages
on invalid input.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

# Ticker validation pattern: 1-5 alphanumeric chars, may include dots for some tickers (BRK.A)
TICKER_PATTERN = re.compile(r'^[A-Z0-9]{1,5}(\.[A-Z])?$')

# Common invalid ticker inputs that should be rejected
INVALID_TICKERS = frozenset({
    '', 'TICKER', 'SYMBOL', 'N/A', 'NA', 'NULL', 'NONE',
    'TEST', 'EXAMPLE', 'XXX', 'UNDEFINED'
})


class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


def validate_ticker(symbol: str, raise_on_invalid: bool = True) -> Optional[str]:
    """
    Validate and normalize a stock ticker symbol.

    Args:
        symbol: Ticker symbol to validate
        raise_on_invalid: If True, raise ValidationError on invalid input.
                         If False, return None instead.

    Returns:
        Normalized ticker symbol (uppercase, stripped) or None if invalid
        and raise_on_invalid is False.

    Raises:
        ValidationError: If symbol is invalid and raise_on_invalid is True.

    Examples:
        >>> validate_ticker("aapl")
        'AAPL'
        >>> validate_ticker("BRK.A")
        'BRK.A'
        >>> validate_ticker("invalid ticker", raise_on_invalid=False)
        None
    """
    if not symbol or not isinstance(symbol, str):
        if raise_on_invalid:
            raise ValidationError("Ticker symbol must be a non-empty string")
        return None

    normalized = symbol.strip().upper()

    if normalized in INVALID_TICKERS:
        if raise_on_invalid:
            raise ValidationError(f"Invalid ticker symbol: '{symbol}'")
        return None

    if not TICKER_PATTERN.match(normalized):
        if raise_on_invalid:
            raise ValidationError(
                f"Invalid ticker format: '{symbol}'. "
                "Must be 1-5 alphanumeric characters (e.g., 'AAPL', 'BRK.A')"
            )
        return None

    return normalized


def validate_tickers(symbols: List[str], skip_invalid: bool = False) -> List[str]:
    """
    Validate and normalize a list of ticker symbols.

    Args:
        symbols: List of ticker symbols to validate
        skip_invalid: If True, silently skip invalid tickers.
                     If False, raise ValidationError on first invalid ticker.

    Returns:
        List of normalized ticker symbols.

    Raises:
        ValidationError: If any symbol is invalid and skip_invalid is False.
    """
    if not isinstance(symbols, (list, tuple)):
        raise ValidationError("Symbols must be a list or tuple")

    validated = []
    for symbol in symbols:
        result = validate_ticker(symbol, raise_on_invalid=not skip_invalid)
        if result is not None:
            validated.append(result)
        elif not skip_invalid:
            # This shouldn't happen since validate_ticker raises, but just in case
            raise ValidationError(f"Invalid ticker: '{symbol}'")

    return validated


def validate_date(date_str: str, formats: Optional[List[str]] = None) -> datetime:
    """
    Validate and parse a date string.

    Args:
        date_str: Date string to validate
        formats: List of acceptable date formats. Defaults to common formats.

    Returns:
        Parsed datetime object.

    Raises:
        ValidationError: If date string cannot be parsed.

    Examples:
        >>> validate_date("2024-01-15")
        datetime.datetime(2024, 1, 15, 0, 0)
        >>> validate_date("01/15/2024")
        datetime.datetime(2024, 1, 15, 0, 0)
    """
    if not date_str or not isinstance(date_str, str):
        raise ValidationError("Date must be a non-empty string")

    if formats is None:
        formats = [
            "%Y-%m-%d",      # ISO format: 2024-01-15
            "%Y/%m/%d",      # 2024/01/15
            "%m/%d/%Y",      # US format: 01/15/2024
            "%d/%m/%Y",      # EU format: 15/01/2024
            "%Y-%m-%dT%H:%M:%S",  # ISO with time
            "%Y-%m-%d %H:%M:%S",  # ISO with time (space)
        ]

    date_str = date_str.strip()

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValidationError(
        f"Invalid date format: '{date_str}'. "
        f"Expected formats: {', '.join(formats[:3])}, etc."
    )


def validate_api_key(key: str, name: str = "API key") -> str:
    """
    Validate an API key is present and non-empty.

    Args:
        key: API key to validate
        name: Name of the key for error messages (e.g., "TWELVE_DATA_API_KEY")

    Returns:
        The API key (stripped).

    Raises:
        ValidationError: If key is empty or None.
    """
    if not key or not isinstance(key, str):
        raise ValidationError(f"{name} is required but not provided")

    key = key.strip()

    if not key:
        raise ValidationError(f"{name} cannot be empty")

    # Basic sanity checks
    if len(key) < 10:
        logger.warning(f"{name} seems unusually short ({len(key)} chars)")

    return key


def validate_positive_number(
    value: float,
    name: str = "value",
    allow_zero: bool = False
) -> float:
    """
    Validate that a number is positive.

    Args:
        value: Number to validate
        name: Name of the value for error messages
        allow_zero: If True, allow zero values

    Returns:
        The validated number.

    Raises:
        ValidationError: If value is not positive (or not non-negative if allow_zero).
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")

    if allow_zero:
        if value < 0:
            raise ValidationError(f"{name} must be non-negative, got {value}")
    else:
        if value <= 0:
            raise ValidationError(f"{name} must be positive, got {value}")

    return float(value)


def validate_range(
    value: float,
    min_val: float,
    max_val: float,
    name: str = "value"
) -> float:
    """
    Validate that a number is within a range.

    Args:
        value: Number to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        name: Name of the value for error messages

    Returns:
        The validated number.

    Raises:
        ValidationError: If value is outside the range.
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")

    if value < min_val or value > max_val:
        raise ValidationError(
            f"{name} must be between {min_val} and {max_val}, got {value}"
        )

    return float(value)
