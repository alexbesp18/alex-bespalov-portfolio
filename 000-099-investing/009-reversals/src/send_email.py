"""
send_email.py — Email formatting and delivery via Resend.

Supports reversal candidate alerts.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any

import requests

logger = logging.getLogger(__name__)


def format_reversals_email(
    candidates: List[Dict[str, Any]],
    date_str: str,
) -> str:
    """Format the reversals email with candidate details."""
    
    lines = [
        f"<h1 style='margin-bottom: 8px;'>Reversal Candidates — {date_str}</h1>",
        "<hr style='border: none; border-top: 2px solid #333;'/>",
        f"<p style='color: #666;'>Found {len(candidates)} potential reversal candidates:</p>",
    ]
    
    if candidates:
        for candidate in candidates:
            ticker = candidate.get('ticker', 'N/A')
            score = candidate.get('score', 0)
            rsi = candidate.get('rsi', 0)
            signal = candidate.get('signal', 'REVERSAL')
            
            color = "#2E8B57" if score > 7 else "#DAA520"
            
            lines.append(f"<div style='margin: 12px 0; padding: 10px; background: #f8f8f8; border-left: 4px solid {color};'>")
            lines.append(f"<strong style='font-size: 16px;'>{ticker}</strong>")
            lines.append(f"<span style='color: {color}; margin-left: 10px;'>{signal}</span><br>")
            lines.append(f"<span style='color: #666; font-size: 12px;'>")
            lines.append(f"Score: {score:.1f} | RSI: {rsi:.1f}")
            if 'close' in candidate:
                lines.append(f" | Close: ${candidate['close']:.2f}")
            lines.append("</span></div>")
    else:
        lines.append("<p style='color: #888;'>No reversal candidates today.</p>")
    
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
    # Test
    test_candidates = [
        {'ticker': 'NVDA', 'score': 8.5, 'rsi': 28, 'close': 140.50, 'signal': 'BULLISH_REVERSAL'},
    ]
    html = format_reversals_email(test_candidates, datetime.now().strftime('%Y-%m-%d'))
    print(html)
