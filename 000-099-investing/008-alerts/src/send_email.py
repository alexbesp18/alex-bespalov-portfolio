"""
send_email.py — Email formatting and delivery via SendGrid.

Supports:
- Main email (4pm): Full signals with click-to-action links
- Reminder email (8am): Summary of yesterday's signals
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

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
    portfolio_signals: List[Dict[str, Any]],
    watchlist_signals: List[Dict[str, Any]],
    no_signal_tickers: List[str],
    date_str: str,
) -> str:
    """Format the main 4pm email with full signal details."""
    
    lines = [
        f"<h1 style='margin-bottom: 8px;'>Trading Signals — {date_str}</h1>",
        "<hr style='border: none; border-top: 2px solid #333;'/>",
    ]
    
    # Portfolio section
    if portfolio_signals or True:  # Always show section header
        lines.append("<h2 style='color: #333; margin-top: 20px;'>PORTFOLIO</h2>")
        lines.append("<hr style='border: none; border-top: 1px solid #999;'/>")
        
        if portfolio_signals:
            # Group by action (SELL first, then BUY)
            sells = [s for s in portfolio_signals if s['action'] == 'SELL']
            buys = [s for s in portfolio_signals if s['action'] == 'BUY']
            
            for signal in sells + buys:
                icon = "▼" if signal['action'] == 'SELL' else "▲"
                color = "#CD5C5C" if signal['action'] == 'SELL' else "#2E8B57"
                action_link = make_action_link(signal['ticker'], signal['signal'])
                
                lines.append(f"<div style='margin: 12px 0;'>")
                lines.append(f"<span style='color: {color}; font-weight: bold;'>{icon} {signal['signal'].replace('_', ' ')}</span><br>")
                lines.append(f"<strong>{signal['ticker']}</strong> — {signal['description']}<br>")
                lines.append(f"<span style='color: #666; font-size: 12px;'>RSI: {signal['flags'].get('rsi')}, Score: {signal['flags'].get('score')}, Close: ${signal['flags'].get('close')}</span><br>")
                lines.append(f"<a href='{action_link}' style='font-size: 12px;'>[ACTIONED: I {'sold' if signal['action'] == 'SELL' else 'bought'}]</a>")
                lines.append("</div>")
        else:
            lines.append("<p style='color: #888;'>No signals</p>")
    
    # Watchlist section
    lines.append("<h2 style='color: #333; margin-top: 24px;'>WATCHLIST</h2>")
    lines.append("<hr style='border: none; border-top: 1px solid #999;'/>")
    
    if watchlist_signals:
        for signal in watchlist_signals:
            icon = "▲"
            color = "#2E8B57"
            action_link = make_action_link(signal['ticker'], signal['signal'])
            
            lines.append(f"<div style='margin: 12px 0;'>")
            lines.append(f"<span style='color: {color}; font-weight: bold;'>{icon} {signal['signal'].replace('_', ' ')}</span><br>")
            lines.append(f"<strong>{signal['ticker']}</strong> — {signal['description']}<br>")
            lines.append(f"<span style='color: #666; font-size: 12px;'>RSI: {signal['flags'].get('rsi')}, Score: {signal['flags'].get('score')}, Close: ${signal['flags'].get('close')}</span><br>")
            lines.append(f"<a href='{action_link}' style='font-size: 12px;'>[ACTIONED: I bought]</a>")
            lines.append("</div>")
    else:
        lines.append("<p style='color: #888;'>No signals</p>")
    
    # No signals footer
    if no_signal_tickers:
        lines.append("<hr style='border: none; border-top: 1px dashed #ccc; margin-top: 20px;'/>")
        lines.append(f"<p style='color: #888; font-size: 12px;'>No signals: {', '.join(no_signal_tickers)}</p>")
    
    return "\n".join(lines)


def format_reminder_email(
    portfolio_signals: List[Dict[str, Any]],
    watchlist_signals: List[Dict[str, Any]],
    date_str: str,
) -> str:
    """Format the 8am reminder email."""
    lines = [
        f"<h1 style='margin-bottom: 8px;'>Reminder — Trading Signals from {date_str}</h1>",
        "<p style='background: #fff8e1; padding: 10px; border: 1px solid #f1e0a6;'>",
        "You had signals yesterday that may need action:",
        "</p>",
    ]
    
    if portfolio_signals:
        lines.append("<h3>PORTFOLIO:</h3>")
        lines.append("<ul>")
        for s in portfolio_signals:
            lines.append(f"<li><strong>{s['action']}</strong>: {s['ticker']} — {s['signal'].replace('_', ' ')}</li>")
        lines.append("</ul>")
    
    if watchlist_signals:
        lines.append("<h3>WATCHLIST:</h3>")
        lines.append("<ul>")
        for s in watchlist_signals:
            lines.append(f"<li><strong>{s['action']}</strong>: {s['ticker']} — {s['signal'].replace('_', ' ')}</li>")
        lines.append("</ul>")
    
    return "\n".join(lines)


class EmailSender:
    """SendGrid email sender."""
    
    def __init__(self, api_key: str, from_email: str, to_email: str):
        self.api_key = api_key
        self.from_email = from_email
        self.to_email = to_email
    
    def send(self, subject: str, html_content: str) -> bool:
        """Send email via SendGrid."""
        if not self.api_key:
            logger.warning("No SendGrid API Key. Logging email content instead.")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body preview: {html_content[:500]}...")
            return False
        
        message = Mail(
            from_email=self.from_email,
            to_emails=self.to_email,
            subject=subject,
            html_content=html_content,
        )
        
        try:
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            logger.info(f"Email sent! Status: {response.status_code}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


if __name__ == "__main__":
    # Test action link
    link = make_action_link("NVDA", "SELL_ALERT")
    print(f"Action link: {link}")
