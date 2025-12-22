"""
Ticker-level trigger evaluation.

Evaluates all signals for a ticker and returns matching triggers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .definitions import PORTFOLIO_SIGNALS, WATCHLIST_SIGNALS
from .conditions import check_conditions, is_in_cooldown, is_suppressed


@dataclass
class TriggerResult:
    """
    Result from trigger evaluation.
    
    Attributes:
        ticker: Stock symbol
        signal: Signal name (e.g., "BUY_PULLBACK")
        action: Action type ("BUY" or "SELL")
        description: Human-readable description
        cooldown_days: Cooldown period
        signal_key: Unique identifier for deduplication
        flags: Relevant flag values at trigger time
    """
    ticker: str
    signal: str
    action: str
    description: str
    cooldown_days: int
    signal_key: str
    flags: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'ticker': self.ticker,
            'signal': self.signal,
            'action': self.action,
            'description': self.description,
            'cooldown_days': self.cooldown_days,
            'signal_key': self.signal_key,
            'flags': self.flags,
        }


def evaluate_ticker(
    ticker: str,
    flags: Dict[str, Any],
    list_type: str,
    cooldowns: Dict[str, str],
    actioned: Dict[str, Any],
    last_run_signals: Optional[List[str]] = None,
) -> List[TriggerResult]:
    """
    Evaluate all signals for a ticker.
    
    Args:
        ticker: Stock symbol
        flags: Dict of current indicator flags and values
        list_type: "portfolio" or "watchlist"
        cooldowns: Current cooldowns dict
        actioned: Actioned/suppressed config
        last_run_signals: Signal keys from last run (for deduplication)
        
    Returns:
        List of TriggerResult for all triggered signals
        
    Example:
        >>> flags = {'above_SMA200': True, 'rsi': 45, 'score': 8}
        >>> results = evaluate_ticker('NVDA', flags, 'watchlist', {}, {})
        >>> for r in results:
        ...     print(f"{r.signal}: {r.description}")
    """
    signals_def = PORTFOLIO_SIGNALS if list_type == 'portfolio' else WATCHLIST_SIGNALS
    results: List[TriggerResult] = []

    for signal_name, signal_config in signals_def.items():
        # Check conditions
        if not check_conditions(flags, signal_config['conditions']):
            continue

        signal_key = f"{ticker}:{signal_name}"

        # Check cooldown
        if is_in_cooldown(signal_key, cooldowns, signal_config['cooldown_days']):
            continue

        # Check suppression
        if is_suppressed(ticker, signal_name, actioned):
            continue

        # Check deduplication
        if last_run_signals and signal_key in last_run_signals:
            continue

        # Signal triggered!
        results.append(TriggerResult(
            ticker=ticker,
            signal=signal_name,
            action=signal_config['action'],
            description=signal_config['description'],
            cooldown_days=signal_config['cooldown_days'],
            signal_key=signal_key,
            flags={
                'rsi': flags.get('rsi'),
                'score': flags.get('score'),
                'close': flags.get('close'),
            },
        ))

    return results


def evaluate_ticker_custom(
    ticker: str,
    flags: Dict[str, Any],
    signal_definitions: Dict[str, Dict[str, Any]],
    cooldowns: Dict[str, str],
    actioned: Dict[str, Any],
    last_run_signals: Optional[List[str]] = None,
) -> List[TriggerResult]:
    """
    Evaluate custom signal definitions for a ticker.
    
    Same as evaluate_ticker but with custom signal definitions.
    
    Args:
        ticker: Stock symbol
        flags: Dict of current indicator flags
        signal_definitions: Custom signal definitions (same format as PORTFOLIO_SIGNALS)
        cooldowns: Current cooldowns dict
        actioned: Actioned/suppressed config
        last_run_signals: Signal keys from last run
        
    Returns:
        List of TriggerResult for all triggered signals
    """
    results: List[TriggerResult] = []

    for signal_name, signal_config in signal_definitions.items():
        if not check_conditions(flags, signal_config['conditions']):
            continue

        signal_key = f"{ticker}:{signal_name}"

        if is_in_cooldown(signal_key, cooldowns, signal_config.get('cooldown_days', 0)):
            continue

        if is_suppressed(ticker, signal_name, actioned):
            continue

        if last_run_signals and signal_key in last_run_signals:
            continue

        results.append(TriggerResult(
            ticker=ticker,
            signal=signal_name,
            action=signal_config.get('action', 'WATCH'),
            description=signal_config.get('description', signal_name),
            cooldown_days=signal_config.get('cooldown_days', 0),
            signal_key=signal_key,
            flags={
                'rsi': flags.get('rsi'),
                'score': flags.get('score'),
                'close': flags.get('close'),
            },
        ))

    return results

