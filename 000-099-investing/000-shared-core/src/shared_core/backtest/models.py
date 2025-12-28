"""
Data models for backtesting.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional
from enum import Enum


class SignalType(Enum):
    UPSIDE_REVERSAL = "upside_reversal"
    DOWNSIDE_REVERSAL = "downside_reversal"
    OVERSOLD = "oversold"


class ConvictionLevel(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


# Trading day counts for each horizon
HORIZON_DAYS = {
    '2w': 10,    # 2 weeks = ~10 trading days
    '2m': 42,    # 2 months = ~42 trading days
    '6m': 126,   # 6 months = ~126 trading days
}


@dataclass
class SignalEvent:
    """A detected signal at a specific point in time."""
    ticker: str
    signal_date: date
    signal_type: SignalType
    conviction: ConvictionLevel
    score: float
    volume_ratio: float
    adx_value: float
    price_at_signal: float

    # Forward returns (filled in after signal detection)
    return_2w: Optional[float] = None   # % return after 2 weeks
    return_2m: Optional[float] = None   # % return after 2 months
    return_6m: Optional[float] = None   # % return after 6 months

    # Additional metrics
    max_gain_2w: Optional[float] = None   # Max gain within 2 weeks
    max_loss_2w: Optional[float] = None   # Max drawdown within 2 weeks
    max_gain_2m: Optional[float] = None
    max_loss_2m: Optional[float] = None
    max_gain_6m: Optional[float] = None
    max_loss_6m: Optional[float] = None

    @property
    def is_winner_2w(self) -> Optional[bool]:
        """True if return positive at 2 week horizon."""
        return self.return_2w > 0 if self.return_2w is not None else None

    @property
    def is_winner_2m(self) -> Optional[bool]:
        return self.return_2m > 0 if self.return_2m is not None else None

    @property
    def is_winner_6m(self) -> Optional[bool]:
        return self.return_6m > 0 if self.return_6m is not None else None


@dataclass
class HorizonMetrics:
    """Metrics for a single time horizon."""
    horizon: str  # '2w', '2m', '6m'
    total_signals: int
    signals_with_data: int  # Signals where we have forward data

    # Win/loss stats
    winners: int
    losers: int
    win_rate: float  # 0-100%

    # Return stats
    avg_return: float       # Average % return
    median_return: float    # Median % return
    best_return: float      # Best single signal return
    worst_return: float     # Worst single signal return

    # Risk stats
    avg_max_gain: float     # Average max gain before horizon
    avg_max_loss: float     # Average max drawdown before horizon

    # Expectancy
    expectancy: float       # (win_rate * avg_win) - (loss_rate * avg_loss)


@dataclass
class BacktestResult:
    """Complete backtest results."""
    # Metadata
    tickers: List[str]
    start_date: date
    end_date: date
    signal_type: SignalType
    conviction_filter: Optional[ConvictionLevel]

    # All signals detected
    signals: List[SignalEvent] = field(default_factory=list)

    # Metrics by horizon
    metrics_2w: Optional[HorizonMetrics] = None
    metrics_2m: Optional[HorizonMetrics] = None
    metrics_6m: Optional[HorizonMetrics] = None

    # Breakdown by conviction
    metrics_by_conviction: Dict[ConvictionLevel, Dict[str, HorizonMetrics]] = field(default_factory=dict)

    @property
    def total_signals(self) -> int:
        return len(self.signals)

    @property
    def high_conviction_signals(self) -> List[SignalEvent]:
        return [s for s in self.signals if s.conviction == ConvictionLevel.HIGH]

    @property
    def medium_conviction_signals(self) -> List[SignalEvent]:
        return [s for s in self.signals if s.conviction == ConvictionLevel.MEDIUM]
