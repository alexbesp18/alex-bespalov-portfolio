"""Tests for input validation."""

import pytest

from src.validation import (
    ValidationError,
    validate_ticker,
    validate_tickers,
    validate_positive_int,
)


class TestValidateTicker:
    """Test single ticker validation."""
    
    def test_valid_ticker(self):
        """Test valid ticker symbols."""
        assert validate_ticker('AAPL') == 'AAPL'
        assert validate_ticker('msft') == 'MSFT'  # lowercased
        assert validate_ticker(' NVDA ') == 'NVDA'  # whitespace
        assert validate_ticker('A') == 'A'  # single char
        assert validate_ticker('BRKA') == 'BRKA'  # Berkshire A
    
    def test_empty_ticker(self):
        """Test that empty ticker raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_ticker('')
        with pytest.raises(ValidationError, match="Invalid ticker format"):
            validate_ticker('   ')  # whitespace-only becomes empty string after strip
    
    def test_too_long_ticker(self):
        """Test that long ticker raises error."""
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            validate_ticker('ABCDEF')
    
    def test_invalid_format_ticker(self):
        """Test invalid ticker formats."""
        with pytest.raises(ValidationError, match="Invalid ticker format"):
            validate_ticker('123')
        with pytest.raises(ValidationError, match="Invalid ticker format"):
            validate_ticker('AAP L')  # space
        with pytest.raises(ValidationError, match="Invalid ticker format"):
            validate_ticker('AAP-L')  # hyphen
        with pytest.raises(ValidationError, match="Invalid ticker format"):
            validate_ticker('AAP.L')  # dot


class TestValidateTickers:
    """Test ticker list validation."""
    
    def test_valid_list(self):
        """Test valid ticker list."""
        result = validate_tickers(['AAPL', 'MSFT', 'NVDA'])
        assert result == ['AAPL', 'MSFT', 'NVDA']
    
    def test_normalizes_list(self):
        """Test that list is normalized."""
        result = validate_tickers(['aapl', ' MSFT ', 'nvda'])
        assert result == ['AAPL', 'MSFT', 'NVDA']
    
    def test_removes_duplicates(self):
        """Test duplicate removal."""
        result = validate_tickers(['AAPL', 'MSFT', 'AAPL'])
        assert result == ['AAPL', 'MSFT']
    
    def test_empty_list(self):
        """Test empty list raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_tickers([])
    
    def test_mixed_invalid(self):
        """Test list with some invalid tickers."""
        with pytest.raises(ValidationError, match="Invalid tickers found"):
            validate_tickers(['AAPL', '123', 'MSFT'])


class TestValidatePositiveInt:
    """Test positive integer validation."""
    
    def test_valid_int(self):
        """Test valid positive integers."""
        assert validate_positive_int(5, 'count') == 5
        assert validate_positive_int(1, 'count') == 1
        assert validate_positive_int(100, 'count', min_val=50) == 100
    
    def test_below_min(self):
        """Test values below minimum."""
        with pytest.raises(ValidationError, match="must be >="):
            validate_positive_int(0, 'count')
        with pytest.raises(ValidationError, match="must be >="):
            validate_positive_int(-1, 'count')
    
    def test_not_int(self):
        """Test non-integer values."""
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_positive_int(3.14, 'count')  # type: ignore
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_positive_int('5', 'count')  # type: ignore
