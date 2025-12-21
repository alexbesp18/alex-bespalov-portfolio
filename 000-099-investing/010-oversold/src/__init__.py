"""Oversold Screener package.

A local CLI tool for ranking stocks by oversold score.

Modules:
    models: Dataclasses for type-safe data passing.
    calculator: Technical indicator calculations.
    fetcher: TwelveData API client.
    oversold_scorer: Weighted oversold scoring logic.

Example:
    >>> from src import OversoldScorer, TechnicalCalculator
    >>> calculator = TechnicalCalculator()
    >>> scorer = OversoldScorer()
"""

from .models import OversoldScore, TickerResult, Watchlist, ScanConfig, OutputFormat
from .oversold_scorer import OversoldScorer
from .calculator import TechnicalCalculator
from .fetcher import TwelveDataFetcher

__all__ = [
    "OversoldScore",
    "TickerResult",
    "Watchlist",
    "ScanConfig",
    "OutputFormat",
    "OversoldScorer",
    "TechnicalCalculator",
    "TwelveDataFetcher",
]
