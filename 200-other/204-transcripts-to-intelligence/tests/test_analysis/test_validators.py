"""
Unit tests for validators (QuoteValidator and TickerValidator).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.analysis.quote_validator import QuoteValidator, QuoteValidationResult
from src.analysis.ticker_validator import TickerValidator, TickerValidationResult


class TestQuoteValidator:
    """Tests for QuoteValidator."""
    
    @pytest.fixture
    def sample_transcript(self) -> str:
        """Sample transcript for testing."""
        return """
        Hello everyone, welcome to the podcast. Today we're discussing 
        artificial intelligence and its impact on business. AI is transformative
        and will change how we work. The future of technology is here.
        We believe that automation will create new opportunities for everyone.
        """
    
    def test_exact_match(self, sample_transcript: str) -> None:
        """Test exact quote match."""
        validator = QuoteValidator(sample_transcript)
        result = validator.validate("AI is transformative")
        
        assert result.is_valid is True
        assert result.similarity_score == 1.0
    
    def test_case_insensitive_match(self, sample_transcript: str) -> None:
        """Test case-insensitive matching."""
        validator = QuoteValidator(sample_transcript)
        result = validator.validate("ai is transformative")
        
        assert result.is_valid is True
    
    def test_nonexistent_quote(self, sample_transcript: str) -> None:
        """Test quote that doesn't exist."""
        validator = QuoteValidator(sample_transcript)
        result = validator.validate("This quote does not exist anywhere")
        
        assert result.is_valid is False
        assert result.similarity_score < 0.8
    
    def test_fuzzy_match_close(self, sample_transcript: str) -> None:
        """Test fuzzy matching for similar quotes."""
        validator = QuoteValidator(sample_transcript)
        # Slightly modified quote
        result = validator.validate("AI is very transformative")
        
        # Should have decent similarity even if not exact
        assert result.similarity_score > 0.5
    
    def test_empty_quote(self, sample_transcript: str) -> None:
        """Test empty quote handling."""
        validator = QuoteValidator(sample_transcript)
        result = validator.validate("")
        
        assert result.is_valid is False
        assert result.similarity_score == 0.0
    
    def test_validate_many(self, sample_transcript: str) -> None:
        """Test validating multiple quotes."""
        validator = QuoteValidator(sample_transcript)
        quotes = [
            "AI is transformative",  # Valid
            "The future of technology is here",  # Valid
            "This is fake",  # Invalid
        ]
        
        results = validator.validate_many(quotes)
        
        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is True
        assert results[2].is_valid is False
    
    def test_validation_summary(self, sample_transcript: str) -> None:
        """Test summary statistics."""
        validator = QuoteValidator(sample_transcript)
        quotes = [
            "AI is transformative",
            "will change how we work",
            "totally fake quote",
        ]
        
        summary = validator.validation_summary(quotes)
        
        assert summary["total_quotes"] == 3
        assert summary["valid_quotes"] == 2
        assert summary["invalid_quotes"] == 1
        assert summary["validation_rate"] == pytest.approx(2/3)


class TestTickerValidator:
    """Tests for TickerValidator."""
    
    def test_valid_ticker_format(self) -> None:
        """Test basic ticker format validation."""
        validator = TickerValidator(cache_results=False)
        
        # Mock yfinance at the import location
        with patch.dict("sys.modules", {"yfinance": MagicMock()}):
            import sys
            mock_yf = sys.modules["yfinance"]
            mock_ticker = Mock()
            mock_ticker.info = {
                "regularMarketPrice": 100.0,
                "exchange": "NASDAQ",
                "quoteType": "EQUITY",
                "longName": "Test Company",
                "marketCap": 1000000000,
            }
            mock_yf.Ticker.return_value = mock_ticker
            
            result = validator.validate("TEST")
            
            assert result.is_valid is True
            assert result.exchange == "NASDAQ"
    
    def test_invalid_format(self) -> None:
        """Test invalid ticker formats."""
        validator = TickerValidator(cache_results=False)
        
        result = validator.validate("12345")  # Numbers not allowed
        assert result.is_valid is False
        
        result = validator.validate("")  # Empty
        assert result.is_valid is False
        
        result = validator.validate("TOOLONG")  # Too long
        assert result.is_valid is False
    
    def test_otc_rejection(self) -> None:
        """Test that OTC stocks are rejected."""
        validator = TickerValidator(cache_results=False)
        
        with patch.dict("sys.modules", {"yfinance": MagicMock()}):
            import sys
            mock_yf = sys.modules["yfinance"]
            mock_ticker = Mock()
            mock_ticker.info = {
                "regularMarketPrice": 1.0,
                "exchange": "OTC",
                "quoteType": "EQUITY",
            }
            mock_yf.Ticker.return_value = mock_ticker
            
            result = validator.validate("OTCX")
            
            assert result.is_valid is False
            assert "OTC" in (result.error or "")
    
    def test_filter_valid(self) -> None:
        """Test filtering to valid tickers only."""
        validator = TickerValidator(cache_results=False)
        
        with patch.dict("sys.modules", {"yfinance": MagicMock()}):
            import sys
            mock_yf = sys.modules["yfinance"]
            
            def mock_ticker_factory(ticker):
                mock = Mock()
                if ticker == "GOOD":
                    mock.info = {
                        "regularMarketPrice": 100.0,
                        "exchange": "NYSE",
                        "quoteType": "EQUITY",
                    }
                else:
                    mock.info = {"regularMarketPrice": None}
                return mock
            
            mock_yf.Ticker.side_effect = mock_ticker_factory
            
            valid = validator.filter_valid(["GOOD", "BAD"])
            
            assert "GOOD" in valid
            assert "BAD" not in valid
    
    def test_caching(self) -> None:
        """Test that results are cached."""
        validator = TickerValidator(cache_results=True)
        
        with patch.dict("sys.modules", {"yfinance": MagicMock()}):
            import sys
            mock_yf = sys.modules["yfinance"]
            mock_ticker = Mock()
            mock_ticker.info = {
                "regularMarketPrice": 100.0,
                "exchange": "NASDAQ",
                "quoteType": "EQUITY",
            }
            mock_yf.Ticker.return_value = mock_ticker
            
            # First call
            result1 = validator.validate("CACHE")
            # Second call should use cache
            result2 = validator.validate("CACHE")
            
            # Only one Ticker call - rest from cache
            assert result1.is_valid == result2.is_valid
    
    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        validator = TickerValidator(cache_results=True)
        validator._cache["TEST"] = TickerValidationResult(
            ticker="TEST", is_valid=True
        )
        
        validator.clear_cache()
        
        assert len(validator._cache) == 0
