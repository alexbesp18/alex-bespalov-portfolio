"""
Condition checking utilities for trigger evaluation.

Provides functions for:
- Multi-condition checking
- Cooldown management
- Suppression (actioned alerts)
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def check_conditions(
    flags: Dict[str, Any],
    conditions: Dict[str, Any],
) -> bool:
    """
    Check if all conditions are met.

    Condition types:
    - Boolean flags: exact match (e.g., 'above_SMA200': True)
    - rsi_min/rsi_max: RSI range check
    - score_min/score_max: Score range check

    Args:
        flags: Dict of current flag values
        conditions: Dict of conditions to check

    Returns:
        True if ALL conditions are met

    Example:
        >>> flags = {'above_SMA200': True, 'rsi': 45, 'score': 7}
        >>> conditions = {'above_SMA200': True, 'rsi_min': 40, 'score_min': 6}
        >>> check_conditions(flags, conditions)
        True
    """
    rsi = flags.get('rsi', 50)
    score = flags.get('score', 0)

    for key, expected in conditions.items():
        if key == 'rsi_min':
            if rsi < expected:
                return False
        elif key == 'rsi_max':
            if rsi > expected:
                return False
        elif key == 'score_min':
            if score < expected:
                return False
        elif key == 'score_max':
            if score > expected:
                return False
        else:
            # Boolean flag
            if flags.get(key) != expected:
                return False

    return True


def is_in_cooldown(
    signal_key: str,
    cooldowns: Dict[str, str],
    cooldown_days: int,
) -> bool:
    """
    Check if a signal is in cooldown period.

    Args:
        signal_key: Unique signal identifier (e.g., "NVDA:BUY_PULLBACK")
        cooldowns: Dict mapping signal_key -> expiry ISO timestamp
        cooldown_days: Cooldown duration from signal config

    Returns:
        True if signal should be suppressed due to cooldown
    """
    if cooldown_days == 0:
        return False

    expiry_str = cooldowns.get(signal_key)
    if not expiry_str:
        return False

    try:
        expiry = datetime.fromisoformat(expiry_str)
        return datetime.now() < expiry
    except ValueError:
        return False


def is_suppressed(
    ticker: str,
    signal_name: str,
    actioned: Dict[str, Any],
) -> bool:
    """
    Check if a signal is suppressed via actioned.json.

    Args:
        ticker: Stock symbol
        signal_name: Signal type name
        actioned: Actioned config dict with 'suppressed' list

    Returns:
        True if signal should be suppressed
    """
    suppressed = actioned.get('suppressed', [])
    today = datetime.now().date()

    for entry in suppressed:
        if entry.get('ticker') != ticker or entry.get('signal') != signal_name:
            continue

        expires_str = entry.get('expires')
        if expires_str:
            try:
                expires = datetime.fromisoformat(expires_str).date()
                if today < expires:
                    return True
            except ValueError:
                pass

    return False


def update_cooldowns(
    cooldowns: Dict[str, str],
    triggered_signals: List[Dict[str, Any]],
) -> Dict[str, str]:
    """
    Update cooldowns for triggered signals.

    Args:
        cooldowns: Current cooldowns dict (modified in place)
        triggered_signals: List of triggered signal dicts with 'signal_key' and 'cooldown_days'

    Returns:
        Updated cooldowns dict
    """
    for signal in triggered_signals:
        cooldown_days = signal.get('cooldown_days', 0)
        if cooldown_days > 0:
            signal_key = signal['signal_key']
            expiry = datetime.now() + timedelta(days=cooldown_days)
            cooldowns[signal_key] = expiry.isoformat()
    return cooldowns


def is_duplicate(
    signal_key: str,
    last_run_signals: Optional[List[str]],
) -> bool:
    """
    Check if signal was already triggered in the last run.

    Args:
        signal_key: Signal identifier to check
        last_run_signals: List of signal keys from last run

    Returns:
        True if this is a duplicate
    """
    if not last_run_signals:
        return False
    return signal_key in last_run_signals

