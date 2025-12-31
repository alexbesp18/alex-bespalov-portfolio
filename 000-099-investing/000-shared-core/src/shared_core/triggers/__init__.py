"""
Trigger evaluation engine for alert systems.

Provides:
- TriggerEngine: Config-driven trigger evaluation
- Condition checking utilities
- Cooldown and suppression management
- Signal definitions
"""

from .conditions import (
    check_conditions,
    is_in_cooldown,
    is_suppressed,
    update_cooldowns,
)
from .definitions import (
    ALL_SIGNALS,
    PORTFOLIO_SIGNALS,
    WATCHLIST_SIGNALS,
)
from .engine import TriggerEngine
from .evaluation import (
    TriggerResult,
    evaluate_ticker,
)

__all__ = [
    # Engine
    "TriggerEngine",
    # Conditions
    "check_conditions",
    "is_in_cooldown",
    "is_suppressed",
    "update_cooldowns",
    # Definitions
    "PORTFOLIO_SIGNALS",
    "WATCHLIST_SIGNALS",
    "ALL_SIGNALS",
    # Evaluation
    "evaluate_ticker",
    "TriggerResult",
]

