"""
Shared data models for investing projects.

Provides:
- TickerResult: Result from scanning a ticker
- Watchlist: Configuration for tickers to watch
- ScanConfig: Scanner configuration
- OutputFormat: Output format enum
"""

# Re-export scoring models for convenience
from ..scoring.models import (
    BullishScore,
    DivergenceResult,
    DivergenceType,
    OversoldScore,
    ReversalScore,
)
from .config import (
    OutputFormat,
    ScanConfig,
)
from .results import (
    ScanResult,
    TickerResult,
)
from .watchlist import (
    Watchlist,
    WatchlistEntry,
)

__all__ = [
    # Results
    "TickerResult",
    "ScanResult",
    # Watchlist
    "WatchlistEntry",
    "Watchlist",
    # Config
    "ScanConfig",
    "OutputFormat",
    # Scoring (re-exports)
    "ReversalScore",
    "OversoldScore",
    "BullishScore",
    "DivergenceResult",
    "DivergenceType",
]

