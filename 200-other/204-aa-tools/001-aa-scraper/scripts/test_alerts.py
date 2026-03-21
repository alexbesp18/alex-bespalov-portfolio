#!/usr/bin/env python3
"""
Alert Testing Script for AA Points Monitor.

Tests email delivery by sending sample alerts.
Useful for verifying Resend configuration.

Usage:
    python scripts/test_alerts.py              # Send test immediate alert
    python scripts/test_alerts.py --digest     # Send test digest
    python scripts/test_alerts.py --reauth     # Send test re-auth notification
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_stacked_deal() -> dict:
    """Create a sample stacked deal for testing."""
    return {
        'merchant_name': 'Test Merchant (Kindle)',
        'portal_rate': 2.0,
        'portal_miles': 10,
        'simplymiles_type': 'flat_bonus',
        'simplymiles_miles': 135,
        'simplymiles_min_spend': 5.0,
        'simplymiles_expires': (datetime.now() + timedelta(days=7)).isoformat(),
        'cc_miles': 5,
        'min_spend_required': 5.0,
        'total_miles': 150,
        'combined_yield': 30.0,
        'deal_score': 42.0,
    }


def create_sample_hotel_deal() -> dict:
    """Create a sample hotel deal for testing."""
    return {
        'hotel_name': 'Test Hotel (Marriott Downtown)',
        'city': 'Las Vegas',
        'state': 'NV',
        'check_in': (datetime.now() + timedelta(days=14)).isoformat(),
        'check_out': (datetime.now() + timedelta(days=16)).isoformat(),
        'nightly_rate': 150.0,
        'base_miles': 3000,
        'bonus_miles': 7000,
        'total_miles': 10000,
        'total_cost': 300.0,
        'yield_ratio': 33.33,
        'deal_score': 38.0,
    }


def test_immediate_alert() -> bool:
    """Send a test immediate alert."""
    from alerts.formatter import format_immediate_alert
    from alerts.sender import send_immediate_alert

    logger.info("Sending test immediate alert...")

    deal = create_sample_stacked_deal()
    content = format_immediate_alert(deal)

    # Modify subject to indicate test
    content['subject'] = f"[TEST] {content['subject']}"

    success = send_immediate_alert(
        subject=content['subject'],
        html_content=content['html'],
        text_content=content['text']
    )

    if success:
        logger.info("Test immediate alert sent successfully!")
    else:
        logger.error("Failed to send test immediate alert")

    return success


def test_digest() -> bool:
    """Send a test daily digest."""
    from alerts.formatter import format_daily_digest
    from alerts.sender import send_digest

    logger.info("Sending test daily digest...")

    stacked = [create_sample_stacked_deal()]
    hotels = [create_sample_hotel_deal()]
    expiring = [create_sample_stacked_deal()]

    content = format_daily_digest(
        stacked_deals=stacked,
        hotel_deals=hotels,
        expiring_deals=expiring,
        health_status={
            'simplymiles': {'is_stale': False, 'age_hours': 1.5},
            'portal': {'is_stale': False, 'age_hours': 3.0},
            'hotels': {'is_stale': True, 'age_hours': 25.0},
        }
    )

    # Modify subject to indicate test
    content['subject'] = f"[TEST] {content['subject']}"

    success = send_digest(
        subject=content['subject'],
        html_content=content['html'],
        text_content=content['text']
    )

    if success:
        logger.info("Test digest sent successfully!")
    else:
        logger.error("Failed to send test digest")

    return success


def test_reauth_notification() -> bool:
    """Send a test re-auth notification."""
    from alerts.sender import send_reauth_notification

    logger.info("Sending test re-auth notification...")

    # Note: This will send the actual re-auth notification format
    # In production, you might want a test-specific version
    success = send_reauth_notification()

    if success:
        logger.info("Test re-auth notification sent successfully!")
    else:
        logger.error("Failed to send test re-auth notification")

    return success


def verify_config() -> bool:
    """Verify email configuration before testing."""
    settings = get_settings()

    logger.info("Verifying email configuration...")
    logger.info(f"  From: {settings.email.from_email}")
    logger.info(f"  To: {settings.email.to_emails}")
    logger.info(f"  API Key: {'*' * 10}... (set)" if settings.email.api_key else "  API Key: NOT SET")

    if not settings.email.api_key:
        logger.error("RESEND_API_KEY is not set!")
        logger.error("Set it in your .env file or environment variables.")
        return False

    if not settings.email.to_emails:
        logger.error("No recipient emails configured!")
        return False

    return True


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="AA Points Monitor - Test Alerts")
    parser.add_argument("--digest", action="store_true", help="Send test digest")
    parser.add_argument("--reauth", action="store_true", help="Send test re-auth notification")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("AA Points Monitor - Alert Testing")
    logger.info("=" * 60)

    # Verify config first
    if not verify_config():
        sys.exit(1)

    success = False

    if args.digest:
        success = test_digest()
    elif args.reauth:
        success = test_reauth_notification()
    else:
        success = test_immediate_alert()

    if success:
        logger.info("\n✅ Test passed! Check your email.")
        sys.exit(0)
    else:
        logger.error("\n❌ Test failed. Check your configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()

