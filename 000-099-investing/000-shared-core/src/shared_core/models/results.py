"""
Result models for scanner outputs.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TickerResult:
    """
    Result from scanning a single ticker.

    Attributes:
        symbol: Ticker symbol
        close: Latest closing price
        rsi: Current RSI value
        score: Bullish score (0-10)
        action: Suggested action (BUY, SELL, HOLD, WATCH)
        message: Human-readable result message
        flags: Dict of computed flags
        matrix: Dict of binary matrix flags
        metadata: Additional metadata (indicator values, etc.)
    """
    symbol: str
    close: float
    rsi: Optional[float] = None
    score: float = 0.0
    action: str = "HOLD"
    message: str = ""
    flags: Dict[str, Any] = field(default_factory=dict)
    matrix: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "close": self.close,
            "rsi": self.rsi,
            "score": self.score,
            "action": self.action,
            "message": self.message,
            "flags": self.flags,
            "matrix": self.matrix,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TickerResult":
        """Create from dictionary."""
        return cls(
            symbol=data.get("symbol", ""),
            close=data.get("close", 0.0),
            rsi=data.get("rsi"),
            score=data.get("score", 0.0),
            action=data.get("action", "HOLD"),
            message=data.get("message", ""),
            flags=data.get("flags", {}),
            matrix=data.get("matrix", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ScanResult:
    """
    Result from a full scan operation.

    Attributes:
        tickers: List of TickerResult objects
        buy_signals: Tickers with BUY action
        sell_signals: Tickers with SELL action
        errors: List of (symbol, error_message) tuples
        scan_time: ISO timestamp of scan
        metadata: Additional scan metadata
    """
    tickers: List[TickerResult] = field(default_factory=list)
    buy_signals: List[TickerResult] = field(default_factory=list)
    sell_signals: List[TickerResult] = field(default_factory=list)
    errors: List[tuple] = field(default_factory=list)
    scan_time: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Populate buy/sell signals from tickers."""
        if not self.buy_signals and not self.sell_signals:
            for t in self.tickers:
                if t.action.upper() == "BUY":
                    self.buy_signals.append(t)
                elif t.action.upper() == "SELL":
                    self.sell_signals.append(t)

    @property
    def has_signals(self) -> bool:
        """Check if any actionable signals exist."""
        return len(self.buy_signals) > 0 or len(self.sell_signals) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tickers": [t.to_dict() for t in self.tickers],
            "buy_signals": [t.to_dict() for t in self.buy_signals],
            "sell_signals": [t.to_dict() for t in self.sell_signals],
            "errors": self.errors,
            "scan_time": self.scan_time,
            "metadata": self.metadata,
        }

