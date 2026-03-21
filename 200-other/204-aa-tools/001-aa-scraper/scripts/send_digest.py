#!/usr/bin/env python3
"""
Daily Digest Sender for AA Points Monitor.

Generates and sends the daily digest email with top opportunities.
Designed to be run via cron at 8am CT.

Usage:
    python scripts/send_digest.py           # Send digest
    python scripts/send_digest.py --preview # Preview without sending
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.logs_path / 'digest.log')
    ]
)
# Suppress httpx verbose logging (logs every HTTP request at INFO level)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def get_digest_data() -> dict:
    """
    Gather all data needed for the daily digest.

    Returns:
        Dict with stacked_deals, hotel_deals, expiring_deals, health_status,
        top_pick, and allocation (arbitrage intelligence)
    """
    from alerts.evaluator import get_full_digest_data
    from alerts.health import HealthMonitor

    logger.info("Gathering digest data with arbitrage intelligence...")

    # Get full digest data including top pick and allocation
    digest_data = get_full_digest_data()

    # Get health status (may override the one from get_full_digest_data)
    monitor = HealthMonitor()
    health_status = monitor.get_freshness_report()

    data = {
        'stacked_deals': digest_data.get('stack', []),
        'hotel_deals': digest_data.get('hotel', []),
        'expiring_deals': digest_data.get('expiring_soon', []),
        'simplymiles_only': digest_data.get('simplymiles_only', []),
        'portal_only': digest_data.get('portal_only', []),
        'health_status': health_status,
        'top_pick': digest_data.get('top_pick'),
        'allocation': digest_data.get('allocation'),
        'new_this_week': digest_data.get('new_this_week', {}),
        'generated_at': datetime.now().isoformat()
    }

    logger.info(f"Digest data gathered:")
    logger.info(f"  - Stacked deals: {len(data['stacked_deals'])}")
    logger.info(f"  - SimplyMiles only: {len(data['simplymiles_only'])}")
    logger.info(f"  - Portal only: {len(data['portal_only'])}")
    logger.info(f"  - Hotel deals: {len(data['hotel_deals'])}")
    logger.info(f"  - Expiring soon: {len(data['expiring_deals'])}")
    new_this_week_count = sum(len(v) for v in data.get('new_this_week', {}).values())
    logger.info(f"  - New this week: {new_this_week_count}")
    if data['top_pick']:
        logger.info(f"  - Top pick: {data['top_pick'].merchant_name} ({data['top_pick'].deal_score:.1f} LP/$)")
    if data['allocation']:
        logger.info(f"  - Allocation: ${data['allocation'].total_spent:.0f} → {data['allocation'].total_miles:,} LPs")

    return data


def generate_digest(data: dict) -> dict:
    """
    Generate the digest email content.

    Args:
        data: Digest data from get_digest_data()

    Returns:
        Dict with subject, html, text
    """
    from alerts.formatter import format_daily_digest

    logger.info("Generating digest content with arbitrage intelligence...")

    # Flatten new_this_week dict into list for formatter
    new_this_week_dict = data.get('new_this_week', {})
    new_this_week_list = []
    if isinstance(new_this_week_dict, dict):
        for deal_type, items in new_this_week_dict.items():
            for item in items:
                item['deal_type'] = deal_type
                new_this_week_list.append(item)

    return format_daily_digest(
        stacked_deals=data['stacked_deals'],
        hotel_deals=data['hotel_deals'],
        expiring_deals=data['expiring_deals'],
        health_status=data['health_status'],
        top_pick=data.get('top_pick'),
        allocation=data.get('allocation'),
        simplymiles_only=data.get('simplymiles_only', []),
        portal_only=data.get('portal_only', []),
        new_this_week=new_this_week_list
    )


def send_digest_email(content: dict) -> bool:
    """
    Send the digest email.

    Args:
        content: Dict with subject, html, text

    Returns:
        True if sent successfully
    """
    from alerts.sender import send_digest

    logger.info("Sending digest email...")

    return send_digest(
        subject=content['subject'],
        html_content=content['html'],
        text_content=content['text']
    )


def run_digest(preview: bool = False) -> dict:
    """
    Run the full digest process.

    Args:
        preview: If True, print digest instead of sending

    Returns:
        Dict with status and details
    """
    result = {
        'status': 'unknown',
        'timestamp': datetime.now().isoformat(),
        'deals_included': 0,
        'sent': False
    }

    try:
        # Gather data
        data = get_digest_data()
        result['deals_included'] = (
            len(data['stacked_deals']) +
            len(data.get('simplymiles_only', [])) +
            len(data.get('portal_only', [])) +
            len(data['hotel_deals'])
        )

        # Generate content
        content = generate_digest(data)

        if preview:
            # Print preview
            print("\n" + "=" * 60)
            print("DIGEST PREVIEW")
            print("=" * 60)
            print(f"\nSubject: {content['subject']}")
            print("\n--- TEXT VERSION ---")
            print(content['text'])
            print("\n--- HTML VERSION ---")
            print("(See HTML file for rendered version)")

            # Optionally save HTML to file
            preview_path = settings.logs_path / 'digest_preview.html'
            with open(preview_path, 'w') as f:
                f.write(content['html'])
            print(f"\nHTML saved to: {preview_path}")

            result['status'] = 'preview'
            result['sent'] = False
        else:
            # Send email
            success = send_digest_email(content)
            result['sent'] = success
            result['status'] = 'success' if success else 'send_failed'

            if success:
                logger.info("Digest sent successfully!")
            else:
                logger.error("Failed to send digest")

    except Exception as e:
        logger.error(f"Digest error: {e}")
        result['status'] = 'error'
        result['error'] = str(e)

    return result


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="AA Points Monitor - Daily Digest")
    parser.add_argument("--preview", action="store_true", help="Preview digest without sending")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("AA Points Monitor - Daily Digest")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    result = run_digest(preview=args.preview)

    logger.info(f"\nResult: {result['status']}")
    logger.info(f"Deals included: {result['deals_included']}")
    logger.info(f"Email sent: {result['sent']}")

    if result['status'] in ['success', 'preview']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

