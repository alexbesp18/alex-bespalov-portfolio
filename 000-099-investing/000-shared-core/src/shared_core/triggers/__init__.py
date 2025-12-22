"""
Trigger evaluation engine for alert systems.

Provides:
- TriggerEngine: Config-driven trigger evaluation
- Condition checking utilities
- Cooldown and suppression management
- Signal definitions
"""

from .engine import TriggerEngine
from .conditions import (
    check_conditions,
    is_in_cooldown,
    is_suppressed,
    update_cooldowns,
)
from .definitions import (
    PORTFOLIO_SIGNALS,
    WATCHLIST_SIGNALS,
)
from .evaluation import (
    evaluate_ticker,
    TriggerResult,
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
    # Evaluation
    "evaluate_ticker",
    "TriggerResult",
]

