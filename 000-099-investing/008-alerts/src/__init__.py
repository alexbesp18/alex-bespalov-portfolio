"""
008-alerts source module.

Re-exports commonly used modules from shared_core for convenience.
Project-specific code remains in this package.
"""

# Re-export from shared_core
from shared_core import (
    # Data Processing
    TechnicalCalculator,
    CacheAwareFetcher,
    process_ohlcv_data,
    add_standard_indicators,
    calculate_matrix,
    calculate_bullish_score,
    # State Management
    StateManager,
    safe_read_json,
    safe_write_json,
    # Triggers
    TriggerEngine,
    check_conditions,
    PORTFOLIO_SIGNALS,
    WATCHLIST_SIGNALS,
    # Notifications
    ResendEmailClient,
    format_html_table,
    # Utils
    get_cached_tickers,
    setup_logging,
)

from shared_core.triggers.conditions import (
    is_in_cooldown,
    is_suppressed,
    update_cooldowns,
)

from shared_core.triggers.evaluation import (
    evaluate_ticker,
    TriggerResult,
)

from shared_core.notifications.resend_client import (
    EmailConfig,
    make_resend_client_from_env,
)

# Project-specific imports
from .fetch_prices import PriceFetcher
from .compute_flags import compute_flags, process_ticker_data
from .send_email import EmailSender, format_main_email, format_reminder_email

__all__ = [
    # shared_core
    "TechnicalCalculator",
    "CacheAwareFetcher",
    "process_ohlcv_data",
    "add_standard_indicators",
    "calculate_matrix",
    "calculate_bullish_score",
    "StateManager",
    "safe_read_json",
    "safe_write_json",
    "TriggerEngine",
    "check_conditions",
    "is_in_cooldown",
    "is_suppressed",
    "update_cooldowns",
    "evaluate_ticker",
    "TriggerResult",
    "PORTFOLIO_SIGNALS",
    "WATCHLIST_SIGNALS",
    "ResendEmailClient",
    "EmailConfig",
    "make_resend_client_from_env",
    "format_html_table",
    "get_cached_tickers",
    "setup_logging",
    # Project-specific
    "PriceFetcher",
    "compute_flags",
    "process_ticker_data",
    "EmailSender",
    "format_main_email",
    "format_reminder_email",
]

