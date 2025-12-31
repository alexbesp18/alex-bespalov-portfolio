"""Data models for the Oversold Screener.

This module contains all dataclasses and type definitions used across
the package. Following Google Python Style Guide for type annotations
and docstrings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class OutputFormat(Enum):
    """Supported output formats for the screener."""
    TABLE = "table"
    JSON = "json"
    CSV = "csv"


@dataclass
class OversoldScore:
    """Result from oversold scoring calculation.
    
    Attributes:
        final_score: The weighted composite score (1.0 to 10.0).
        components: Individual indicator scores before weighting.
        raw_values: Actual indicator values from the data.
    """
    final_score: float
    components: Dict[str, float]
    raw_values: Dict[str, float]


@dataclass
class TickerResult:
    """Complete analysis result for a single ticker.
    
    Attributes:
        ticker: Stock symbol (e.g., "NVDA").
        score: Oversold score (1.0 to 10.0, higher = more oversold).
        rsi: Raw RSI value.
        williams_r: Raw Williams %R value.
        stoch_k: Raw Stochastic %K value.
        price: Current closing price.
        components: Score breakdown by indicator.
    """
    ticker: str
    score: float
    rsi: float
    williams_r: float
    stoch_k: float
    price: float
    components: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "ticker": self.ticker,
            "score": self.score,
            "rsi": self.rsi,
            "williams_r": self.williams_r,
            "stoch_k": self.stoch_k,
            "price": self.price,
            "components": self.components,
        }


@dataclass
class Watchlist:
    """A named collection of ticker symbols.
    
    Attributes:
        name: Human-readable name (e.g., "AI Infrastructure").
        tickers: List of stock symbols.
    """
    name: str
    tickers: List[str]


@dataclass
class ScanConfig:
    """Configuration for a screening run.
    
    Attributes:
        watchlist_names: Names of watchlists to scan.
        top_n: Number of top results to return.
        output_format: How to format the output.
        verbose: Whether to show detailed breakdowns.
    """
    watchlist_names: List[str]
    top_n: int = 10
    output_format: OutputFormat = OutputFormat.TABLE
    verbose: bool = False
