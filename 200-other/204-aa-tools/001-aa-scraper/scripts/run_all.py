#!/usr/bin/env python3
"""
Full Pipeline Runner for AA Points Monitor.

Runs all scrapers, detects opportunities, and sends immediate alerts.
Designed for manual runs and cron job orchestration.

Usage:
    python scripts/run_all.py              # Full run
    python scripts/run_all.py --scrapers   # Only run scrapers
    python scripts/run_all.py --detect     # Only run detection
    python scripts/run_all.py --alerts     # Only check/send alerts
"""

import argparse
import asyncio
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
        logging.FileHandler(settings.logs_path / 'run_all.log')
    ]
)
# Suppress httpx verbose logging (logs every HTTP request at INFO level)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def run_simplymiles_scraper() -> dict:
    """Run the SimplyMiles scraper (API-based for speed and reliability)."""
    from scrapers.simplymiles_api import run_scraper
    logger.info("Running SimplyMiles API scraper...")
    return await run_scraper(test_mode=False)


async def run_portal_scraper() -> dict:
    """Run the Portal scraper."""
    from scrapers.portal import run_scraper
    logger.info("Running Portal scraper...")
    return await run_scraper(test_mode=False)


async def run_hotels_scraper() -> dict:
    """Run the Hotels scraper."""
    from scrapers.hotels import run_scraper
    logger.info("Running Hotels scraper...")
    # run_scraper is sync, so run in thread pool
    return await asyncio.to_thread(run_scraper, test_mode=False)


def run_stack_detection() -> dict:
    """Run stack detection."""
    from core.stack_detector import run_detection
    logger.info("Running stack detection...")
    return run_detection(store_results=True)


def check_and_send_alerts() -> dict:
    """Check for alertable deals and send ONE rich batched immediate alert."""
    from alerts.evaluator import get_full_immediate_alert_data, record_alerts
    from alerts.formatter import format_batch_alert
    from alerts.sender import send_immediate_alert
    from alerts.health import check_and_alert

    logger.info("Checking for alertable deals...")

    result = {
        'alerts_sent': 0,
        'deals_checked': 0,
        'health_alerts': 0
    }

    # Check health first
    health_result = check_and_alert()
    result['health_alerts'] = health_result.get('alerts_sent', 0)

    # Get full alert data (all deal types for rich immediate alerts)
    alert_data = get_full_immediate_alert_data()

    alertable_stack = alert_data.get('alertable_stack', [])
    alertable_hotel = alert_data.get('alertable_hotel', [])

    result['deals_checked'] = len(alertable_stack) + len(alertable_hotel)

    # Only send if there are alertable deals (above threshold + not in cooldown)
    if alert_data.get('has_alerts'):
        try:
            # Format rich batched email with ALL deal types
            email_content = format_batch_alert(
                stack_deals=alert_data.get('stack', []),
                hotel_deals=alert_data.get('hotel', []),
                simplymiles_only=alert_data.get('simplymiles_only', []),
                portal_only=alert_data.get('portal_only', []),
                context=alert_data.get('context', {})
            )

            # Send ONE rich alert
            success = send_immediate_alert(
                subject=email_content['subject'],
                html_content=email_content['html'],
                text_content=email_content['text']
            )

            if success:
                # Record alertable deals (for cooldown tracking)
                if alertable_stack:
                    record_alerts(alertable_stack, alert_type='immediate', deal_type='stack')
                if alertable_hotel:
                    record_alerts(alertable_hotel, alert_type='immediate', deal_type='hotel')
                result['alerts_sent'] = 1

                total_deals = (
                    len(alert_data.get('stack', [])) +
                    len(alert_data.get('simplymiles_only', [])) +
                    len(alert_data.get('portal_only', [])) +
                    len(alert_data.get('hotel', []))
                )
                logger.info(f"Sent rich alert with {total_deals} deals across all categories")

        except Exception as e:
            logger.error(f"Error sending batched alert: {e}")

    logger.info(f"Alerts check complete: {result['alerts_sent']} email(s) sent")
    return result


async def run_all_scrapers() -> dict:
    """Run all scrapers sequentially."""
    results = {
        'simplymiles': None,
        'portal': None,
        'hotels': None,
        'start_time': datetime.now().isoformat(),
        'end_time': None
    }

    # Run scrapers sequentially (to avoid rate limiting issues)
    try:
        results['simplymiles'] = await run_simplymiles_scraper()
    except Exception as e:
        logger.error(f"SimplyMiles scraper failed: {e}")
        results['simplymiles'] = {'status': 'error', 'error': str(e)}

    try:
        results['portal'] = await run_portal_scraper()
    except Exception as e:
        logger.error(f"Portal scraper failed: {e}")
        results['portal'] = {'status': 'error', 'error': str(e)}

    try:
        results['hotels'] = await run_hotels_scraper()
    except Exception as e:
        logger.error(f"Hotels scraper failed: {e}")
        results['hotels'] = {'status': 'error', 'error': str(e)}

    results['end_time'] = datetime.now().isoformat()

    return results


def run_full_pipeline() -> dict:
    """Run the complete pipeline: scrape -> detect -> alert."""
    logger.info("=" * 60)
    logger.info("AA Points Monitor - Full Pipeline Run")
    logger.info("=" * 60)

    results = {
        'timestamp': datetime.now().isoformat(),
        'scrapers': None,
        'detection': None,
        'alerts': None,
        'status': 'unknown'
    }

    # Step 1: Run all scrapers
    logger.info("\n[Step 1/3] Running scrapers...")
    try:
        results['scrapers'] = asyncio.run(run_all_scrapers())
    except Exception as e:
        logger.error(f"Scrapers failed: {e}")
        results['scrapers'] = {'status': 'error', 'error': str(e)}

    # Step 2: Run stack detection
    logger.info("\n[Step 2/3] Running stack detection...")
    try:
        results['detection'] = run_stack_detection()
    except Exception as e:
        logger.error(f"Detection failed: {e}")
        results['detection'] = {'status': 'error', 'error': str(e)}

    # Step 3: Check and send alerts
    logger.info("\n[Step 3/3] Checking and sending alerts...")
    try:
        results['alerts'] = check_and_send_alerts()
    except Exception as e:
        logger.error(f"Alerts failed: {e}")
        results['alerts'] = {'status': 'error', 'error': str(e)}

    # Determine overall status
    all_success = (
        results['scrapers'] and results['scrapers'].get('simplymiles', {}).get('status') == 'success' and
        results['detection'] and results['detection'].get('status') == 'success'
    )

    results['status'] = 'success' if all_success else 'partial_failure'

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Pipeline Summary")
    logger.info("=" * 60)

    if results['scrapers']:
        sm = results['scrapers'].get('simplymiles', {})
        portal = results['scrapers'].get('portal', {})
        hotels = results['scrapers'].get('hotels', {})

        logger.info(f"SimplyMiles: {sm.get('status', 'unknown')} ({sm.get('offers_scraped', 0)} offers)")
        logger.info(f"Portal: {portal.get('status', 'unknown')} ({portal.get('stores_scraped', 0)} stores)")
        logger.info(f"Hotels: {hotels.get('status', 'unknown')} ({hotels.get('hotels_scraped', 0)} hotels)")

    if results['detection']:
        det = results['detection']
        logger.info(f"Detection: {det.get('status', 'unknown')} ({det.get('total_opportunities', 0)} opportunities)")
        logger.info(f"  - Above immediate threshold: {det.get('above_immediate_threshold', 0)}")
        logger.info(f"  - Expiring soon: {det.get('expiring_soon', 0)}")

    if results['alerts']:
        logger.info(f"Alerts sent: {results['alerts'].get('alerts_sent', 0)}")

    logger.info("=" * 60)

    return results


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="AA Points Monitor - Full Pipeline")
    parser.add_argument("--scrapers", action="store_true", help="Only run scrapers")
    parser.add_argument("--detect", action="store_true", help="Only run detection")
    parser.add_argument("--alerts", action="store_true", help="Only check/send alerts")
    args = parser.parse_args()

    # If specific mode requested, run only that
    if args.scrapers:
        results = asyncio.run(run_all_scrapers())
        logger.info(f"Scrapers complete: {results}")
    elif args.detect:
        results = run_stack_detection()
        logger.info(f"Detection complete: {results}")
    elif args.alerts:
        results = check_and_send_alerts()
        logger.info(f"Alerts complete: {results}")
    else:
        # Run full pipeline
        results = run_full_pipeline()

    # Exit with appropriate code
    if results.get('status') == 'success':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

