"""
Email sender for AA Points Monitor.
Uses Resend API for reliable email delivery.
"""

import html
import logging
from typing import List, Optional

import resend

from config.settings import get_settings

logger = logging.getLogger(__name__)


def init_resend():
    """Initialize Resend with API key."""
    settings = get_settings()

    if not settings.email.api_key:
        logger.warning("RESEND_API_KEY not set - emails will not be sent")
        return False

    resend.api_key = settings.email.api_key
    return True


def send_email(
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    to_emails: Optional[List[str]] = None
) -> bool:
    """
    Send an email via Resend.

    Args:
        subject: Email subject line
        html_content: HTML body content
        text_content: Plain text body (optional, for fallback)
        to_emails: List of recipient emails (defaults to config)

    Returns:
        True if sent successfully
    """
    settings = get_settings()

    if not init_resend():
        return False

    to_emails = to_emails or settings.email.to_emails

    if not to_emails:
        logger.error("No recipient emails configured")
        return False

    try:
        params = {
            "from": settings.email.from_email,
            "to": to_emails,
            "subject": subject,
            "html": html_content,
        }

        if text_content:
            params["text"] = text_content

        response = resend.Emails.send(params)

        logger.info(f"Email sent successfully: {subject}")
        logger.debug(f"Resend response: {response}")

        return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def send_immediate_alert(
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send an immediate alert email.

    Wrapper around send_email with immediate alert styling.
    """
    return send_email(
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )


def send_digest(
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send the daily digest email.

    Wrapper around send_email for digest.
    """
    return send_email(
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )


def get_session_age_info() -> str:
    """Get session age information for alerts."""
    try:
        from scripts.session_keepalive import get_session_age_days, load_session_tracking
        age = get_session_age_days()
        tracking = load_session_tracking()

        if age:
            return f"Session age: {age:.1f} days"
        elif tracking.get("last_successful_scrape"):
            return f"Last successful scrape: {tracking['last_successful_scrape']}"
        return "Session age: Unknown"
    except:
        return "Session age: Unknown"


def send_reauth_notification() -> bool:
    """
    Send notification that SimplyMiles re-authentication is needed.
    Includes VNC connection details for VPS users.
    """
    settings = get_settings()
    session_info = get_session_age_info()

    subject = "⚠️ Action Required: SimplyMiles Session Expired"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #d32f2f;">⚠️ Action Required: SimplyMiles Session Expired</h2>

        <p>Your SimplyMiles session has expired. The scraper cannot access your offers until you re-authenticate.</p>

        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin: 16px 0;">
            <strong>{session_info}</strong>
        </div>

        <h3>Option 1: Quick Re-Auth (Recommended)</h3>
        <ol>
            <li>SSH into your VPS: <code>ssh root@REDACTED_VPS_IP</code></li>
            <li>Run: <code>cd ~/aa_scraper && python scripts/quick_reauth.py</code></li>
            <li>Connect via VNC to complete login</li>
        </ol>

        <h3>Option 2: VNC Direct Access</h3>
        <div style="background: #e3f2fd; padding: 12px; border-radius: 4px; margin: 12px 0;">
            <p style="margin: 0;"><strong>VNC Connection:</strong></p>
            <code style="display: block; margin-top: 8px;">
                Host: REDACTED_VPS_IP:5900<br>
                Password: REDACTED_VNC_PASS
            </code>
            <p style="margin: 8px 0 0 0; font-size: 13px;">
                Use any VNC client (RealVNC, TigerVNC, macOS Screen Sharing)
            </p>
        </div>

        <h3>Option 3: Manual Setup</h3>
        <ol>
            <li>SSH into VPS: <code>ssh root@REDACTED_VPS_IP</code></li>
            <li>Start Xvfb: <code>Xvfb :99 -screen 0 1280x800x24 &</code></li>
            <li>Export display: <code>export DISPLAY=:99</code></li>
            <li>Run: <code>cd ~/aa_scraper && python scripts/setup_auth.py</code></li>
            <li>Connect via VNC to complete the login</li>
        </ol>

        <p style="color: #666; font-size: 14px; margin-top: 20px;">
            This typically happens every 7-30 days due to AA SSO token expiration.
            The scraper will resume automatically after re-authentication.
        </p>

        <p style="color: #999; font-size: 12px; margin-top: 10px;">
            Tip: The session_keepalive cron job runs every 6 hours to extend your session.
            If you keep getting these emails, check that the cron job is running.
        </p>
    </div>
    """

    text_content = f"""
⚠️ ACTION REQUIRED: SimplyMiles Session Expired

Your SimplyMiles session has expired. The scraper cannot access your offers.

{session_info}

OPTION 1: Quick Re-Auth (Recommended)
1. SSH: ssh root@REDACTED_VPS_IP
2. Run: cd ~/aa_scraper && python scripts/quick_reauth.py
3. Connect via VNC to complete login

OPTION 2: VNC Direct Access
Host: REDACTED_VPS_IP:5900
Password: REDACTED_VNC_PASS

OPTION 3: Manual Setup
1. SSH: ssh root@REDACTED_VPS_IP
2. Xvfb :99 -screen 0 1280x800x24 &
3. export DISPLAY=:99
4. cd ~/aa_scraper && python scripts/setup_auth.py
5. Connect via VNC to complete login

This typically happens every 7-30 days. The scraper resumes automatically after re-auth.
    """

    return send_email(
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )


def send_health_alert(
    scraper_name: str,
    failure_count: int,
    last_error: Optional[str] = None
) -> bool:
    """
    Send notification about scraper health issues.

    Args:
        scraper_name: Name of the failing scraper
        failure_count: Number of consecutive failures
        last_error: Most recent error message
    """
    subject = f"⚠️ AA Monitor: {scraper_name.title()} Scraper Failing"

    error_section = ""
    if last_error:
        escaped_error = html.escape(str(last_error))
        error_section = f"""
        <h3>Last Error:</h3>
        <pre style="background: #f5f5f5; padding: 10px; overflow-x: auto;">{escaped_error}</pre>
        """

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #d32f2f;">⚠️ Scraper Health Alert</h2>

        <p>The <strong>{scraper_name}</strong> scraper has failed <strong>{failure_count}</strong> consecutive times.</p>

        {error_section}

        <h3>Possible Causes:</h3>
        <ul>
            <li>Website structure changed (selectors need updating)</li>
            <li>Rate limiting or IP blocking</li>
            <li>Session expired (for SimplyMiles)</li>
            <li>Network connectivity issues</li>
        </ul>

        <p>Check the logs for more details: <code>/var/log/aa-monitor/{scraper_name}.log</code></p>
    </div>
    """

    text_content = f"""
    ⚠️ SCRAPER HEALTH ALERT

    The {scraper_name} scraper has failed {failure_count} consecutive times.

    Last Error: {last_error or 'No error message available'}

    Check logs for details.
    """

    return send_email(
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )


async def send_reauth_notification_async():
    """Async wrapper for send_reauth_notification."""
    import asyncio
    return await asyncio.get_event_loop().run_in_executor(None, send_reauth_notification)

