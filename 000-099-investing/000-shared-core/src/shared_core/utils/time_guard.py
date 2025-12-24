"""
Time guard utilities for scheduled execution.

Useful for cron jobs that need to run at specific local times,
especially when handling DST transitions.
"""

import logging
from datetime import datetime
from typing import Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore[no-redef]

logger = logging.getLogger(__name__)


def check_time_guard(
    expected_hour: int,
    timezone_name: str = "America/Chicago",
    now: Optional[datetime] = None,
) -> bool:
    """
    Check if the current local hour matches the expected hour.

    Used to guard cron jobs that may be triggered multiple times
    during DST transitions.

    Args:
        expected_hour: Expected local hour (0-23)
        timezone_name: IANA timezone name (default: America/Chicago)
        now: Optional current time (for testing). Defaults to system time.

    Returns:
        True if current local hour matches expected hour.

    Example:
        >>> # In cron job
        >>> if not check_time_guard(16, "America/Chicago"):
        ...     logger.info("Skipping - not 4pm CT")
        ...     return
    """
    try:
        if now is None:
            local_now = datetime.now(ZoneInfo(timezone_name))
        else:
            local_now = now.astimezone(ZoneInfo(timezone_name))

        if local_now.hour != expected_hour:
            logger.info(
                f"Time guard: local hour is {local_now.hour} in {timezone_name}; "
                f"expected {expected_hour}. Skipping."
            )
            return False
        return True

    except Exception as e:
        logger.warning(f"Time guard check failed (tz={timezone_name}): {e}. Allowing execution.")
        return True


def is_market_hours(timezone_name: str = "America/New_York") -> bool:
    """
    Check if current time is during US market hours.

    Market hours: 9:30 AM - 4:00 PM Eastern, Monday-Friday

    Args:
        timezone_name: IANA timezone for market (default: America/New_York)

    Returns:
        True if currently during market hours.
    """
    try:
        now = datetime.now(ZoneInfo(timezone_name))

        # Weekday check (0=Monday, 4=Friday)
        if now.weekday() > 4:
            return False

        # Time check (9:30 - 16:00)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

        return market_open <= now <= market_close

    except Exception:
        return False

