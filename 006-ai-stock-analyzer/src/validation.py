"""
Input validation utilities.

Provides validation functions for user inputs with
clear error messages.
"""

import re
from typing import List

from src.constants import TICKER_MAX_LENGTH, TICKER_PATTERN


class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


def validate_ticker(ticker: str) -> str:
    """
    Validate and normalize a stock ticker symbol.
    
    Args:
        ticker: Raw ticker string
        
    Returns:
        Normalized ticker (uppercase, stripped)
        
    Raises:
        ValidationError: If ticker is invalid
    """
    if not ticker:
        raise ValidationError("Ticker cannot be empty")
    
    # Normalize
    ticker = ticker.strip().upper()
    
    # Check length
    if len(ticker) > TICKER_MAX_LENGTH:
        raise ValidationError(
            f"Ticker '{ticker}' exceeds maximum length of {TICKER_MAX_LENGTH}"
        )
    
    # Check format
    if not re.match(TICKER_PATTERN, ticker):
        raise ValidationError(
            f"Invalid ticker format: '{ticker}'. "
            "Expected 1-5 uppercase letters (e.g., 'AAPL', 'MSFT')"
        )
    
    return ticker


def validate_tickers(tickers: List[str]) -> List[str]:
    """
    Validate and normalize a list of tickers.
    
    Args:
        tickers: List of raw ticker strings
        
    Returns:
        List of normalized tickers
        
    Raises:
        ValidationError: If any ticker is invalid
    """
    if not tickers:
        raise ValidationError("Ticker list cannot be empty")
    
    validated = []
    errors = []
    
    for i, ticker in enumerate(tickers):
        try:
            validated.append(validate_ticker(ticker))
        except ValidationError as e:
            errors.append(f"  [{i}] {e}")
    
    if errors:
        raise ValidationError(
            f"Invalid tickers found:\n" + "\n".join(errors)
        )
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for t in validated:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    
    return unique


def validate_positive_int(value: int, name: str, min_val: int = 1) -> int:
    """
    Validate a positive integer.
    
    Args:
        value: Integer to validate
        name: Parameter name for error messages
        min_val: Minimum allowed value
        
    Returns:
        Validated integer
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer, got {type(value).__name__}")
    
    if value < min_val:
        raise ValidationError(f"{name} must be >= {min_val}, got {value}")
    
    return value
