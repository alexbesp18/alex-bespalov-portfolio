"""
Ticker Validator

Validates stock tickers against US exchanges (NYSE, NASDAQ, AMEX).
Uses yfinance to verify tickers exist and are actively traded.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Set

__all__ = ["TickerValidator", "TickerValidationResult"]

logger = logging.getLogger(__name__)

# Valid US exchanges
VALID_EXCHANGES = {
    "NYSE", "NASDAQ", "AMEX", "NYSEARCA", "BATS", 
    "NMS",  # NASDAQ National Market System
    "NGM",  # NASDAQ Global Market
    "NCM",  # NASDAQ Capital Market
}

# Known invalid patterns (OTC, pink sheets, etc.)
INVALID_PATTERNS = {
    "OTC", "PINK", "GREY", "QB", "QX",
}


@dataclass
class TickerValidationResult:
    """Result of validating a single ticker.
    
    Attributes:
        ticker: The ticker symbol.
        is_valid: True if ticker is valid US exchange stock.
        exchange: Exchange where ticker is listed.
        company_name: Full company name (if found).
        market_cap: Market cap in billions (if available).
        error: Error message if validation failed.
    """
    ticker: str
    is_valid: bool
    exchange: Optional[str] = None
    company_name: Optional[str] = None
    market_cap: Optional[float] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "is_valid": self.is_valid,
            "exchange": self.exchange,
            "company_name": self.company_name,
            "market_cap": self.market_cap,
            "error": self.error,
        }


class TickerValidator:
    """Validates stock tickers against US exchanges.
    
    Uses yfinance to fetch ticker information and validate
    that stocks are traded on major US exchanges.
    
    Example:
        >>> validator = TickerValidator()
        >>> result = validator.validate("NVDA")
        >>> print(f"{result.ticker}: {result.is_valid} ({result.exchange})")
    """
    
    def __init__(self, cache_results: bool = True):
        """Initialize validator.
        
        Args:
            cache_results: Whether to cache validation results.
        """
        self.cache_results = cache_results
        self._cache: Dict[str, TickerValidationResult] = {}
    
    def validate(self, ticker: str) -> TickerValidationResult:
        """Validate a single ticker.
        
        Args:
            ticker: Stock ticker symbol.
            
        Returns:
            TickerValidationResult with validation details.
        """
        ticker = ticker.upper().strip()
        
        # Check cache
        if self.cache_results and ticker in self._cache:
            return self._cache[ticker]
        
        # Basic format validation
        if not ticker or not ticker.isalpha() or len(ticker) > 5:
            result = TickerValidationResult(
                ticker=ticker,
                is_valid=False,
                error="Invalid ticker format",
            )
            if self.cache_results:
                self._cache[ticker] = result
            return result
        
        try:
            import yfinance as yf
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Check if we got valid data
            if not info or info.get("regularMarketPrice") is None:
                result = TickerValidationResult(
                    ticker=ticker,
                    is_valid=False,
                    error="Ticker not found or no market data",
                )
            else:
                exchange = info.get("exchange", "").upper()
                quote_type = info.get("quoteType", "")
                
                # Check for OTC/pink sheets
                is_otc = any(p in exchange for p in INVALID_PATTERNS)
                is_valid_exchange = any(e in exchange for e in VALID_EXCHANGES)
                is_equity = quote_type == "EQUITY"
                
                is_valid = is_valid_exchange and not is_otc and is_equity
                
                market_cap = info.get("marketCap")
                if market_cap:
                    market_cap = market_cap / 1e9  # Convert to billions
                
                result = TickerValidationResult(
                    ticker=ticker,
                    is_valid=is_valid,
                    exchange=exchange,
                    company_name=info.get("longName") or info.get("shortName"),
                    market_cap=round(market_cap, 2) if market_cap else None,
                    error=None if is_valid else f"Invalid exchange: {exchange}",
                )
                
        except ImportError:
            logger.warning("yfinance not installed, skipping validation")
            result = TickerValidationResult(
                ticker=ticker,
                is_valid=True,  # Assume valid if can't check
                error="yfinance not available",
            )
        except Exception as e:
            logger.warning(f"Error validating {ticker}: {e}")
            result = TickerValidationResult(
                ticker=ticker,
                is_valid=False,
                error=str(e),
            )
        
        if self.cache_results:
            self._cache[ticker] = result
        
        return result
    
    def validate_many(self, tickers: List[str]) -> List[TickerValidationResult]:
        """Validate multiple tickers.
        
        Args:
            tickers: List of ticker symbols.
            
        Returns:
            List of validation results.
        """
        return [self.validate(t) for t in tickers]
    
    def filter_valid(self, tickers: List[str]) -> List[str]:
        """Filter to only valid tickers.
        
        Args:
            tickers: List of ticker symbols.
            
        Returns:
            List of valid tickers only.
        """
        results = self.validate_many(tickers)
        return [r.ticker for r in results if r.is_valid]
    
    def validation_summary(self, tickers: List[str]) -> Dict[str, Any]:
        """Get summary of ticker validation.
        
        Args:
            tickers: List of tickers to validate.
            
        Returns:
            Summary with counts and details.
        """
        results = self.validate_many(tickers)
        
        valid = [r for r in results if r.is_valid]
        invalid = [r for r in results if not r.is_valid]
        
        return {
            "total_tickers": len(results),
            "valid_count": len(valid),
            "invalid_count": len(invalid),
            "valid_tickers": [r.ticker for r in valid],
            "invalid_tickers": [
                {"ticker": r.ticker, "reason": r.error} 
                for r in invalid
            ],
            "total_market_cap_billions": sum(
                r.market_cap or 0 for r in valid
            ),
        }
    
    def clear_cache(self):
        """Clear the validation cache."""
        self._cache.clear()
