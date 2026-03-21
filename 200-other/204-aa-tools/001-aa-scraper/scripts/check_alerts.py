#!/usr/bin/env python3
"""
Check for pending immediate alerts and send them.

This script is designed to be run by cron every 2 hours (or as configured).
It checks for deals above immediate alert thresholds and sends email notifications.

Usage:
    python scripts/check_alerts.py           # Send pending alerts
    python scripts/check_alerts.py --dry-run # Preview without sending
"""

import argparse
import logging
import sys
from datetime import datetime

# Set up logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Suppress httpx verbose logging (logs every HTTP request at INFO level)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from alerts.evaluator import get_pending_immediate_alerts, record_alerts
from alerts.formatter import format_batch_alert
from alerts.sender import send_immediate_alert
from alerts.push import push_hot_deal, push_hotel_deal


def check_and_send_alerts(dry_run: bool = False) -> dict:
    """
    Check for pending immediate alerts and send them.

    Args:
        dry_run: If True, don't actually send emails

    Returns:
        Dict with counts of alerts found and sent
    """
    results = {
        'stack_found': 0,
        'stack_sent': 0,
        'stack_push': 0,
        'hotel_found': 0,
        'hotel_sent': 0,
        'hotel_push': 0,
        'errors': []
    }

    try:
        # Get pending alerts
        pending = get_pending_immediate_alerts()

        # Process stacked deal alerts
        stack_alerts = pending.get('stack', [])
        results['stack_found'] = len(stack_alerts)

        if stack_alerts:
            logger.info(f"Found {len(stack_alerts)} stacked deal alerts")

            if dry_run:
                logger.info("DRY RUN - Would send stacked deal alerts:")
                for deal in stack_alerts[:5]:
                    logger.info(f"  • {deal.get('merchant_name')}: {deal.get('deal_score', 0):.1f} LP/$")
            else:
                # Format and send batched alert
                formatted = format_batch_alert(stack_alerts, deal_type='stack')

                if send_immediate_alert(
                    subject=formatted['subject'],
                    html_content=formatted['html'],
                    text_content=formatted.get('text', '')
                ):
                    record_alerts(stack_alerts, alert_type='immediate', deal_type='stack')
                    results['stack_sent'] = len(stack_alerts)
                    logger.info(f"Sent alert for {len(stack_alerts)} stacked deals")

                    # Send push notification for top deal
                    if stack_alerts:
                        top_deal = stack_alerts[0]
                        if push_hot_deal(
                            merchant=top_deal.get('merchant_name', 'Unknown'),
                            yield_ratio=top_deal.get('deal_score', 0),
                            min_spend=top_deal.get('min_spend_required', 0),
                            total_miles=top_deal.get('total_miles', 0)
                        ):
                            results['stack_push'] = 1
                else:
                    results['errors'].append("Failed to send stacked deal alert email")

        # Process hotel alerts
        hotel_alerts = pending.get('hotel', [])
        results['hotel_found'] = len(hotel_alerts)

        if hotel_alerts:
            logger.info(f"Found {len(hotel_alerts)} hotel deal alerts")

            if dry_run:
                logger.info("DRY RUN - Would send hotel deal alerts:")
                for deal in hotel_alerts[:5]:
                    logger.info(f"  • {deal.get('hotel_name')}: {deal.get('deal_score', 0):.1f} LP/$")
            else:
                # Format and send batched alert
                formatted = format_batch_alert(hotel_alerts, deal_type='hotel')

                if send_immediate_alert(
                    subject=formatted['subject'],
                    html_content=formatted['html'],
                    text_content=formatted.get('text', '')
                ):
                    record_alerts(hotel_alerts, alert_type='immediate', deal_type='hotel')
                    results['hotel_sent'] = len(hotel_alerts)
                    logger.info(f"Sent alert for {len(hotel_alerts)} hotel deals")

                    # Send push notification for top hotel deal
                    if hotel_alerts:
                        top_hotel = hotel_alerts[0]
                        if push_hotel_deal(
                            hotel=top_hotel.get('hotel_name', 'Unknown'),
                            city=top_hotel.get('city', ''),
                            yield_ratio=top_hotel.get('deal_score', 0),
                            total_cost=top_hotel.get('total_cost', 0),
                            total_miles=top_hotel.get('total_miles', 0)
                        ):
                            results['hotel_push'] = 1
                else:
                    results['errors'].append("Failed to send hotel deal alert email")

        if not stack_alerts and not hotel_alerts:
            logger.info("No pending immediate alerts found")

    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        results['errors'].append(str(e))

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Check for pending immediate alerts and send them"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview alerts without sending"
    )

    args = parser.parse_args()

    logger.info(f"=== Alert Check Started at {datetime.now().isoformat()} ===")

    results = check_and_send_alerts(dry_run=args.dry_run)

    # Summary
    total_found = results['stack_found'] + results['hotel_found']
    total_sent = results['stack_sent'] + results['hotel_sent']

    if args.dry_run:
        logger.info(f"DRY RUN complete: {total_found} alerts would be sent")
    else:
        logger.info(f"Alert check complete: {total_sent}/{total_found} alerts sent")

    if results['errors']:
        logger.error(f"Errors encountered: {results['errors']}")
        sys.exit(1)

    logger.info(f"=== Alert Check Completed ===")


if __name__ == "__main__":
    main()
