"""
Shared data models for investing projects.

Provides:
- TickerResult: Result from scanning a ticker
- Watchlist: Configuration for tickers to watch
- ScanConfig: Scanner configuration
- OutputFormat: Output format enum
"""

from .results import (
    TickerResult,
    ScanResult,
)
from .watchlist import (
    WatchlistEntry,
    Watchlist,
)
from .config import (
    ScanConfig,
    OutputFormat,
)

# Re-export scoring models for convenience
from ..scoring.models import (
    ReversalScore,
    OversoldScore,
    BullishScore,
    DivergenceResult,
    DivergenceType,
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

