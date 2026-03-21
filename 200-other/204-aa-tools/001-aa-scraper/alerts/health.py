"""
Health monitoring for AA Points Monitor.
Tracks scraper health, session status, and sends alerts on failures.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from config.settings import get_settings
from core.database import get_database

logger = logging.getLogger(__name__)

# Session age warning threshold (days)
SESSION_AGE_WARNING_DAYS = 5


def get_session_status() -> Dict[str, Any]:
    """
    Get SimplyMiles session status including age and last activity.

    Returns:
        Dict with session health information
    """
    try:
        from scripts.session_keepalive import (
            get_session_age_days,
            load_session_tracking
        )

        tracking = load_session_tracking()
        age = get_session_age_days()

        return {
            "session_age_days": age,
            "last_auth": tracking.get("last_auth"),
            "last_keepalive": tracking.get("last_keepalive"),
            "last_successful_scrape": tracking.get("last_successful_scrape"),
            "needs_attention": age is not None and age > SESSION_AGE_WARNING_DAYS,
            "status": "healthy" if age and age <= SESSION_AGE_WARNING_DAYS else "warning" if age else "unknown"
        }
    except Exception as e:
        logger.debug(f"Could not get session status: {e}")
        return {
            "session_age_days": None,
            "last_auth": None,
            "last_keepalive": None,
            "last_successful_scrape": None,
            "needs_attention": False,
            "status": "unknown"
        }


class HealthMonitor:
    """Monitor scraper health, session status, and send alerts on failures."""

    def __init__(self):
        self.settings = get_settings()
        self.db = get_database()

    def check_scraper_health(self, scraper_name: str) -> Dict[str, Any]:
        """
        Check health status of a scraper.

        Args:
            scraper_name: Name of the scraper

        Returns:
            Dict with health status
        """
        failures = self.db.get_consecutive_failures(scraper_name)
        last_success = self.db.get_last_successful_scrape(scraper_name)
        is_stale = self.db.is_data_stale(scraper_name)

        status = {
            'scraper': scraper_name,
            'consecutive_failures': failures,
            'last_success': last_success,
            'is_stale': is_stale,
            'needs_attention': failures >= self.settings.health.failure_threshold,
            'checked_at': datetime.now().isoformat()
        }

        return status

    def check_all_scrapers(self) -> Dict[str, Dict[str, Any]]:
        """
        Check health status of all scrapers.

        Returns:
            Dict mapping scraper name to health status
        """
        scrapers = ['simplymiles', 'portal', 'hotels']
        health = {}

        for scraper in scrapers:
            health[scraper] = self.check_scraper_health(scraper)

        return health

    def should_send_health_alert(self, scraper_name: str) -> bool:
        """
        Check if we should send a health alert for this scraper.

        Args:
            scraper_name: Name of the scraper

        Returns:
            True if alert should be sent
        """
        status = self.check_scraper_health(scraper_name)
        return status['needs_attention']

    def send_health_alerts_if_needed(self) -> int:
        """
        Check all scrapers and send alerts for any that need attention.

        Returns:
            Number of alerts sent
        """
        from alerts.sender import send_health_alert

        alerts_sent = 0
        health = self.check_all_scrapers()

        for scraper_name, status in health.items():
            if status['needs_attention']:
                logger.warning(f"Scraper {scraper_name} needs attention: {status['consecutive_failures']} failures")

                # Get last error message
                last_error = None
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT error_message FROM scraper_health
                        WHERE scraper_name = ? AND status = 'failure'
                        ORDER BY run_at DESC LIMIT 1
                    """, (scraper_name,))
                    result = cursor.fetchone()
                    if result:
                        last_error = result['error_message']

                # Send alert
                success = send_health_alert(
                    scraper_name=scraper_name,
                    failure_count=status['consecutive_failures'],
                    last_error=last_error
                )

                if success:
                    alerts_sent += 1

        return alerts_sent

    def get_freshness_report(self) -> Dict[str, Dict[str, Any]]:
        """
        Get data freshness report for all sources.

        Returns:
            Dict with freshness info per source
        """
        return self.db.get_data_freshness_report()

    def check_session_health(self) -> Dict[str, Any]:
        """
        Check SimplyMiles session health.

        Returns:
            Dict with session status
        """
        return get_session_status()

    def get_status_summary(self) -> str:
        """
        Get a human-readable status summary.

        Returns:
            Status summary string
        """
        health = self.check_all_scrapers()
        freshness = self.get_freshness_report()
        session = self.check_session_health()

        lines = ["AA Points Monitor - Health Status", "=" * 40]

        # Session status
        lines.append("\nSIMPLYMILES SESSION")
        if session.get("session_age_days"):
            age = session["session_age_days"]
            session_icon = "⚠️" if session.get("needs_attention") else "✅"
            lines.append(f"  Status: {session_icon} {session.get('status', 'unknown').upper()}")
            lines.append(f"  Age: {age:.1f} days")
            if age > SESSION_AGE_WARNING_DAYS:
                lines.append(f"  ⚠️  Consider proactive re-authentication")
        else:
            lines.append("  Status: ❓ Unknown (no tracking data)")

        if session.get("last_successful_scrape"):
            lines.append(f"  Last scrape: {session['last_successful_scrape']}")

        # Scraper status
        for scraper in ['simplymiles', 'portal', 'hotels']:
            h = health.get(scraper, {})
            f = freshness.get(scraper, {})

            status_icon = "✅" if not h.get('needs_attention') else "⚠️"
            stale_icon = "⚠️" if f.get('is_stale') else "✅"

            lines.append(f"\n{scraper.upper()}")
            lines.append(f"  Status: {status_icon} {'OK' if not h.get('needs_attention') else 'NEEDS ATTENTION'}")
            lines.append(f"  Failures: {h.get('consecutive_failures', 0)}")
            lines.append(f"  Data: {stale_icon} {'STALE' if f.get('is_stale') else 'Fresh'}")

            if f.get('age_hours'):
                lines.append(f"  Age: {f['age_hours']:.1f} hours")

        return "\n".join(lines)


def check_and_alert() -> Dict[str, Any]:
    """
    Run health check and send alerts if needed.
    Includes session health monitoring with proactive warnings.

    Returns:
        Dict with check results
    """
    monitor = HealthMonitor()

    result = {
        'timestamp': datetime.now().isoformat(),
        'health': monitor.check_all_scrapers(),
        'freshness': monitor.get_freshness_report(),
        'session': monitor.check_session_health(),
        'alerts_sent': 0
    }

    # Send scraper health alerts if needed
    result['alerts_sent'] = monitor.send_health_alerts_if_needed()

    # Session status is tracked in result['session'] for status reports,
    # but we don't send proactive warnings - the 10-min ping catches actual failures

    return result


if __name__ == "__main__":
    # Print status when run directly
    logging.basicConfig(level=logging.INFO)

    monitor = HealthMonitor()
    print(monitor.get_status_summary())

