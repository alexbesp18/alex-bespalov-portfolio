"""
send_email.py — Email formatting and delivery via Resend.

Supports:
- Main email (4pm): Full signals with click-to-action links
- Reminder email (8am): Summary of yesterday's signals
"""

import os
import logging
from typing import Dict, List, Any
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

# GitHub repo for action links (update this)
GITHUB_REPO = os.environ.get("GITHUB_REPO", "alexbespalov/alex-bespalov-portfolio")


def make_action_link(ticker: str, signal: str) -> str:
    """Generate GitHub Issue URL for click-to-action."""
    title = f"ACTIONED:{ticker}:{signal}"
    params = urlencode({
        'title': title,
        'labels': 'actioned'
    })
    return f"https://github.com/{GITHUB_REPO}/issues/new?{params}"


def format_main_email(
    signals: List[Dict[str, Any]],
    no_signal_tickers: List[str],
    date_str: str,
) -> str:
    """Format the main 4pm email with full signal details."""

    # Group by action (SELL first, then BUY)
    sells = [s for s in signals if s['action'] == 'SELL']
    buys = [s for s in signals if s['action'] == 'BUY']

    lines = [
        f"<h1 style='margin-bottom: 8px;'>Trading Signals — {date_str}</h1>",
        f"<p style='color: #666;'>{len(buys)} BUY signals, {len(sells)} SELL signals</p>",
        "<hr style='border: none; border-top: 2px solid #333;'/>",
    ]

    # SELL signals first (most urgent)
    if sells:
        lines.append("<h2 style='color: #CD5C5C; margin-top: 20px;'>⚠️ SELL SIGNALS</h2>")
        lines.append("<hr style='border: none; border-top: 1px solid #CD5C5C;'/>")

        for signal in sells:
            action_link = make_action_link(signal['ticker'], signal['signal'])

            lines.append("<div style='margin: 12px 0; padding: 10px; background: #fff5f5; border-left: 3px solid #CD5C5C;'>")
            lines.append(f"<span style='color: #CD5C5C; font-weight: bold;'>▼ {signal['signal'].replace('_', ' ')}</span><br>")
            lines.append(f"<strong>{signal['ticker']}</strong> — {signal['description']}<br>")
            lines.append(f"<span style='color: #666; font-size: 12px;'>RSI: {signal['flags'].get('rsi')}, Score: {signal['flags'].get('score')}, Close: ${signal['flags'].get('close')}</span><br>")
            lines.append(f"<a href='{action_link}' style='font-size: 12px;'>[ACTIONED: I sold]</a>")
            lines.append("</div>")

    # BUY signals
    if buys:
        lines.append("<h2 style='color: #2E8B57; margin-top: 24px;'>📈 BUY SIGNALS</h2>")
        lines.append("<hr style='border: none; border-top: 1px solid #2E8B57;'/>")

        for signal in buys:
            action_link = make_action_link(signal['ticker'], signal['signal'])

            lines.append("<div style='margin: 12px 0; padding: 10px; background: #f5fff5; border-left: 3px solid #2E8B57;'>")
            lines.append(f"<span style='color: #2E8B57; font-weight: bold;'>▲ {signal['signal'].replace('_', ' ')}</span><br>")
            lines.append(f"<strong>{signal['ticker']}</strong> — {signal['description']}<br>")
            lines.append(f"<span style='color: #666; font-size: 12px;'>RSI: {signal['flags'].get('rsi')}, Score: {signal['flags'].get('score')}, Close: ${signal['flags'].get('close')}</span><br>")
            lines.append(f"<a href='{action_link}' style='font-size: 12px;'>[ACTIONED: I bought]</a>")
            lines.append("</div>")

    if not signals:
        lines.append("<p style='color: #888;'>No signals today</p>")

    # No signals footer (collapsed)
    if no_signal_tickers and len(no_signal_tickers) < 50:
        lines.append("<hr style='border: none; border-top: 1px dashed #ccc; margin-top: 20px;'/>")
        lines.append(f"<p style='color: #888; font-size: 12px;'>No signals: {', '.join(no_signal_tickers)}</p>")
    elif no_signal_tickers:
        lines.append("<hr style='border: none; border-top: 1px dashed #ccc; margin-top: 20px;'/>")
        lines.append(f"<p style='color: #888; font-size: 12px;'>No signals for {len(no_signal_tickers)} other tickers</p>")

    return "\n".join(lines)


def format_reminder_email(
    signals: List[Dict[str, Any]],
    date_str: str,
) -> str:
    """Format the 8am reminder email."""
    sells = [s for s in signals if s['action'] == 'SELL']
    buys = [s for s in signals if s['action'] == 'BUY']

    lines = [
        f"<h1 style='margin-bottom: 8px;'>Reminder — Trading Signals from {date_str}</h1>",
        "<p style='background: #fff8e1; padding: 10px; border: 1px solid #f1e0a6;'>",
        "You had signals yesterday that may need action:",
        "</p>",
    ]

    if sells:
        lines.append("<h3 style='color: #CD5C5C;'>SELL:</h3>")
        lines.append("<ul>")
        for s in sells:
            lines.append(f"<li><strong>{s['ticker']}</strong> — {s['signal'].replace('_', ' ')}</li>")
        lines.append("</ul>")

    if buys:
        lines.append("<h3 style='color: #2E8B57;'>BUY:</h3>")
        lines.append("<ul>")
        for s in buys:
            lines.append(f"<li><strong>{s['ticker']}</strong> — {s['signal'].replace('_', ' ')}</li>")
        lines.append("</ul>")

    return "\n".join(lines)


class EmailSender:
    """Resend email sender."""

    def __init__(self, api_key: str, from_email: str, to_emails: str | List[str]):
        self.api_key = api_key
        self.from_email = from_email
        # Support both single email and list of emails
        if isinstance(to_emails, str):
            self.to_emails = [to_emails] if to_emails else []
        else:
            self.to_emails = to_emails or []

    def send(self, subject: str, html_content: str) -> bool:
        """Send email via Resend."""
        if not self.api_key:
            logger.warning("No Resend API Key. Logging email content instead.")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body preview: {html_content[:500]}...")
            return False

        if not self.to_emails:
            logger.warning("No recipients specified. Skipping email.")
            return False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "from": self.from_email,
            "to": self.to_emails,
            "subject": subject,
            "html": html_content,
        }

        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Email sent via Resend! Status: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email: {e}")
            return False


if __name__ == "__main__":
    # Test action link
    link = make_action_link("NVDA", "SELL_ALERT")
    print(f"Action link: {link}")
