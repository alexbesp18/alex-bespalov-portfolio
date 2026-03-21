"""
Push notification support for AA Points Monitor.
Uses ntfy.sh for free, simple push notifications.

Setup:
1. Install ntfy app on your phone (iOS/Android)
2. Subscribe to your topic (e.g., 'aa-points-alex')
3. Set NTFY_TOPIC in your .env file

Alternatively, supports Pushover ($5 one-time):
1. Create Pushover account
2. Set PUSHOVER_USER_KEY and PUSHOVER_APP_TOKEN in .env
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def get_ntfy_topic() -> Optional[str]:
    """Get ntfy topic from environment."""
    return os.environ.get('NTFY_TOPIC')


def get_pushover_config() -> tuple[Optional[str], Optional[str]]:
    """Get Pushover credentials from environment."""
    return (
        os.environ.get('PUSHOVER_USER_KEY'),
        os.environ.get('PUSHOVER_APP_TOKEN')
    )


def send_push(
    title: str,
    message: str,
    priority: int = 0,
    tags: Optional[list[str]] = None,
    click_url: Optional[str] = None
) -> bool:
    """
    Send a push notification.

    Tries ntfy first, falls back to Pushover if configured.

    Args:
        title: Notification title
        message: Notification body
        priority: -2 to 2 (-2=min, 0=default, 2=urgent)
        tags: List of emoji tags for ntfy (e.g., ['dollar', 'chart'])
        click_url: URL to open when notification is clicked

    Returns:
        True if notification was sent successfully
    """
    # Try ntfy first
    ntfy_topic = get_ntfy_topic()
    if ntfy_topic:
        return send_ntfy(title, message, priority, tags, click_url)

    # Try Pushover
    user_key, app_token = get_pushover_config()
    if user_key and app_token:
        return send_pushover(title, message, priority)

    logger.warning("No push notification service configured. "
                   "Set NTFY_TOPIC or PUSHOVER_* in .env")
    return False


def send_ntfy(
    title: str,
    message: str,
    priority: int = 0,
    tags: Optional[list[str]] = None,
    click_url: Optional[str] = None
) -> bool:
    """
    Send notification via ntfy.sh.

    Args:
        title: Notification title
        message: Notification body
        priority: -2 to 2 (maps to ntfy's min/low/default/high/urgent)
        tags: List of emoji tags
        click_url: URL to open on click
    """
    topic = get_ntfy_topic()
    if not topic:
        logger.warning("NTFY_TOPIC not set")
        return False

    # Map priority to ntfy values
    priority_map = {
        -2: '1',  # min
        -1: '2',  # low
        0: '3',   # default
        1: '4',   # high
        2: '5'    # urgent
    }
    ntfy_priority = priority_map.get(priority, '3')

    headers = {
        'Title': title,
        'Priority': ntfy_priority,
    }

    if tags:
        headers['Tags'] = ','.join(tags)

    if click_url:
        headers['Click'] = click_url

    try:
        response = httpx.post(
            f'https://ntfy.sh/{topic}',
            content=message,
            headers=headers,
            timeout=10.0
        )
        response.raise_for_status()
        logger.info(f"Push sent via ntfy: {title}")
        return True
    except Exception as e:
        logger.error(f"Failed to send ntfy notification: {e}")
        return False


def send_pushover(
    title: str,
    message: str,
    priority: int = 0
) -> bool:
    """
    Send notification via Pushover.

    Args:
        title: Notification title
        message: Notification body
        priority: -2 to 2 (Pushover native values)
    """
    user_key, app_token = get_pushover_config()
    if not user_key or not app_token:
        logger.warning("Pushover credentials not configured")
        return False

    try:
        response = httpx.post(
            'https://api.pushover.net/1/messages.json',
            data={
                'token': app_token,
                'user': user_key,
                'title': title,
                'message': message,
                'priority': priority,
            },
            timeout=10.0
        )
        response.raise_for_status()
        logger.info(f"Push sent via Pushover: {title}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Pushover notification: {e}")
        return False


# Convenience functions for common alert types

def push_hot_deal(
    merchant: str,
    yield_ratio: float,
    min_spend: float,
    total_miles: int
) -> bool:
    """Send push for a hot stacked deal."""
    return send_push(
        title=f"🔥 Hot Deal: {merchant}",
        message=f"{yield_ratio:.1f} LP/$ • Spend ${min_spend:.0f} → {total_miles:,} LPs",
        priority=1,
        tags=['dollar', 'fire']
    )


def push_hotel_deal(
    hotel: str,
    city: str,
    yield_ratio: float,
    total_cost: float,
    total_miles: int
) -> bool:
    """Send push for a hotel deal."""
    return send_push(
        title=f"🏨 Hotel: {city}",
        message=f"{hotel[:30]}{'...' if len(hotel) > 30 else ''}\n"
                f"{yield_ratio:.1f} LP/$ • ${total_cost:.0f} → {total_miles:,} LPs",
        priority=1,
        tags=['hotel', 'moneybag']
    )


def push_expiring_soon(
    merchant: str,
    yield_ratio: float,
    hours_left: int
) -> bool:
    """Send push for expiring deal."""
    return send_push(
        title=f"⏰ Expiring: {merchant}",
        message=f"{yield_ratio:.1f} LP/$ • Only {hours_left}h left!",
        priority=2,  # Urgent
        tags=['warning', 'clock']
    )


def push_system_alert(
    title: str,
    message: str
) -> bool:
    """Send system/health alert."""
    return send_push(
        title=f"⚠️ {title}",
        message=message,
        priority=0,
        tags=['warning']
    )
