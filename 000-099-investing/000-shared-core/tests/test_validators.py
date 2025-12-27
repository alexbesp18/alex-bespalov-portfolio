"""Tests for input validation utilities."""

import pytest
from datetime import datetime

from shared_core.validators import (
    ValidationError,
    validate_ticker,
    validate_tickers,
    validate_date,
    validate_api_key,
    validate_positive_number,
    validate_range,
)


class TestValidateTicker:
    """Tests for validate_ticker function."""

    def test_valid_ticker_uppercase(self):
        """Valid uppercase ticker passes."""
        assert validate_ticker("AAPL") == "AAPL"

    def test_valid_ticker_lowercase_normalized(self):
        """Lowercase ticker is normalized to uppercase."""
        assert validate_ticker("aapl") == "AAPL"

    def test_valid_ticker_with_dot(self):
        """Ticker with class suffix (BRK.A) passes."""
        assert validate_ticker("BRK.A") == "BRK.A"

    def test_valid_ticker_numbers(self):
        """Ticker with numbers passes."""
        assert validate_ticker("X") == "X"
        assert validate_ticker("F") == "F"

    def test_invalid_empty_raises(self):
        """Empty string raises ValidationError."""
        with pytest.raises(ValidationError, match="non-empty string"):
            validate_ticker("")

    def test_invalid_none_raises(self):
        """None raises ValidationError."""
        with pytest.raises(ValidationError, match="non-empty string"):
            validate_ticker(None)  # type: ignore

    def test_invalid_too_long_raises(self):
        """Ticker longer than 5 chars raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid ticker format"):
            validate_ticker("TOOLONG")

    def test_invalid_special_chars_raises(self):
        """Ticker with special characters raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid ticker format"):
            validate_ticker("AA$PL")

    def test_reserved_words_raises(self):
        """Reserved words like 'TICKER' raise ValidationError."""
        with pytest.raises(ValidationError, match="Invalid ticker"):
            validate_ticker("TICKER")

    def test_invalid_returns_none_when_not_raising(self):
        """Invalid ticker returns None when raise_on_invalid=False."""
        assert validate_ticker("invalid ticker", raise_on_invalid=False) is None
        assert validate_ticker("", raise_on_invalid=False) is None

    def test_whitespace_stripped(self):
        """Whitespace is stripped from ticker."""
        assert validate_ticker("  AAPL  ") == "AAPL"


class TestValidateTickers:
    """Tests for validate_tickers function."""

    def test_valid_list(self):
        """Valid list of tickers passes."""
        result = validate_tickers(["AAPL", "GOOG", "MSFT"])
        assert result == ["AAPL", "GOOG", "MSFT"]

    def test_normalizes_case(self):
        """Tickers are normalized to uppercase."""
        result = validate_tickers(["aapl", "goog"])
        assert result == ["AAPL", "GOOG"]

    def test_invalid_in_list_raises(self):
        """Invalid ticker in list raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_tickers(["AAPL", "invalid ticker", "GOOG"])

    def test_skip_invalid_filters(self):
        """skip_invalid=True filters out invalid tickers."""
        result = validate_tickers(
            ["AAPL", "invalid", "GOOG", ""],
            skip_invalid=True
        )
        assert result == ["AAPL", "GOOG"]

    def test_not_list_raises(self):
        """Non-list input raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a list"):
            validate_tickers("AAPL")  # type: ignore


class TestValidateDate:
    """Tests for validate_date function."""

    def test_iso_format(self):
        """ISO format date parses correctly."""
        result = validate_date("2024-01-15")
        assert result == datetime(2024, 1, 15)

    def test_us_format(self):
        """US format (MM/DD/YYYY) parses correctly."""
        result = validate_date("01/15/2024")
        assert result == datetime(2024, 1, 15)

    def test_iso_with_time(self):
        """ISO format with time parses correctly."""
        result = validate_date("2024-01-15T14:30:00")
        assert result == datetime(2024, 1, 15, 14, 30, 0)

    def test_invalid_format_raises(self):
        """Invalid date format raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_date("not a date")

    def test_empty_raises(self):
        """Empty string raises ValidationError."""
        with pytest.raises(ValidationError, match="non-empty string"):
            validate_date("")

    def test_whitespace_stripped(self):
        """Whitespace is stripped from date string."""
        result = validate_date("  2024-01-15  ")
        assert result == datetime(2024, 1, 15)


class TestValidateApiKey:
    """Tests for validate_api_key function."""

    def test_valid_key(self):
        """Valid API key passes."""
        result = validate_api_key("sk-1234567890abcdef")
        assert result == "sk-1234567890abcdef"

    def test_empty_raises(self):
        """Empty key raises ValidationError."""
        with pytest.raises(ValidationError, match="required"):
            validate_api_key("")

    def test_none_raises(self):
        """None raises ValidationError."""
        with pytest.raises(ValidationError, match="required"):
            validate_api_key(None)  # type: ignore

    def test_whitespace_only_raises(self):
        """Whitespace-only key raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_api_key("   ")

    def test_custom_name_in_error(self):
        """Custom name appears in error message."""
        with pytest.raises(ValidationError, match="TWELVE_DATA_KEY"):
            validate_api_key("", name="TWELVE_DATA_KEY")


class TestValidatePositiveNumber:
    """Tests for validate_positive_number function."""

    def test_positive_int(self):
        """Positive integer passes."""
        assert validate_positive_number(10) == 10.0

    def test_positive_float(self):
        """Positive float passes."""
        assert validate_positive_number(10.5) == 10.5

    def test_zero_not_allowed_by_default(self):
        """Zero raises ValidationError by default."""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_positive_number(0)

    def test_zero_allowed_when_specified(self):
        """Zero passes when allow_zero=True."""
        assert validate_positive_number(0, allow_zero=True) == 0.0

    def test_negative_raises(self):
        """Negative number raises ValidationError."""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_positive_number(-5)

    def test_non_number_raises(self):
        """Non-number raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_positive_number("10")  # type: ignore


class TestValidateRange:
    """Tests for validate_range function."""

    def test_within_range(self):
        """Value within range passes."""
        assert validate_range(5, 0, 10) == 5.0

    def test_at_min_boundary(self):
        """Value at minimum boundary passes."""
        assert validate_range(0, 0, 10) == 0.0

    def test_at_max_boundary(self):
        """Value at maximum boundary passes."""
        assert validate_range(10, 0, 10) == 10.0

    def test_below_min_raises(self):
        """Value below minimum raises ValidationError."""
        with pytest.raises(ValidationError, match="must be between"):
            validate_range(-1, 0, 10)

    def test_above_max_raises(self):
        """Value above maximum raises ValidationError."""
        with pytest.raises(ValidationError, match="must be between"):
            validate_range(11, 0, 10)

    def test_non_number_raises(self):
        """Non-number raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_range("5", 0, 10)  # type: ignore
