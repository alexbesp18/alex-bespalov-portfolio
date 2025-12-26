import os
import logging
import resend
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Email configuration - defaults for local dev, override via environment
FROM_EMAIL = os.environ.get("SENDER_EMAIL", "alerts@example.com")
TO_EMAILS = os.environ.get("NOTIFICATION_EMAILS", "").split(",") if os.environ.get("NOTIFICATION_EMAILS") else []


class Notifier:
    def __init__(self, api_key: str, from_email: str = None, to_emails: List[str] = None):
        self.api_key = api_key
        self.from_email = from_email or FROM_EMAIL
        self.to_emails = to_emails or TO_EMAILS
        if api_key:
            resend.api_key = api_key

    def format_email_body(self, results: List[Dict], mode: str = "main") -> tuple:
        """
        Formats the oversold results into an HTML email body.
        
        Args:
            results: List of dicts with oversold scores and data
            mode: "main" or "reminder"
        
        Returns:
            (html_body, count)
        """
        mode = (mode or "main").lower()
        
        # Sort by oversold score descending
        sorted_results = sorted(results, key=lambda x: x.get('oversold_score', 0), reverse=True)
        
        body = "<h1 style='margin-bottom: 6px;'>Oversold Opportunities</h1>"
        body += f"<p style='margin-top: 0; color: #666;'>Daily Oversold Screener | {datetime.now().strftime('%Y-%m-%d')}</p>"

        if mode == "reminder":
            body += (
                "<p style='background: #fff8e1; padding: 10px; border: 1px solid #f1e0a6;'>"
                "<strong>Reminder</strong>: these are the oversold candidates from the last scan."
                "</p>"
            )
        else:
            body += (
                "<p style='background: #e3f2fd; padding: 10px; border: 1px solid #bbdefb;'>"
                "Stocks ranked by <strong>Oversold Score</strong> (1-10). "
                "Higher scores indicate stronger oversold conditions with potential bounce setups."
                "</p>"
            )
        
        if not sorted_results:
            body += "<p>No oversold candidates found today.</p>"
            return body, 0
        
        # Create table
        body += """
        <table style='border-collapse: collapse; font-size: 12px; width: 100%; margin-top: 20px;'>
        <thead>
            <tr style='background: #1a237e; color: white;'>
                <th style='padding: 8px; border: 1px solid #333; text-align: left;'>Symbol</th>
                <th style='padding: 8px; border: 1px solid #333;'>Score</th>
                <th style='padding: 8px; border: 1px solid #333;'>Price</th>
                <th style='padding: 8px; border: 1px solid #333;'>RSI</th>
                <th style='padding: 8px; border: 1px solid #333;'>%Off High</th>
                <th style='padding: 8px; border: 1px solid #333;'>Williams %R</th>
                <th style='padding: 8px; border: 1px solid #333;'>%Below SMA200</th>
            </tr>
        </thead>
        <tbody>
        """
        
        for row in sorted_results:
            score = row.get('oversold_score', 0)
            
            # Color coding based on score
            if score >= 8:
                bg_color = "#c8e6c9"  # Strong green
                score_color = "#1b5e20"
            elif score >= 6:
                bg_color = "#e8f5e9"  # Light green
                score_color = "#2e7d32"
            elif score >= 4:
                bg_color = "#fff8e1"  # Light yellow
                score_color = "#f57f17"
            else:
                bg_color = "#fff"
                score_color = "#666"
            
            symbol = row.get('symbol', '')
            price = row.get('price', row.get('close', 0))
            rsi = row.get('rsi', row.get('RSI', 'N/A'))
            pct_off_high = row.get('pct_off_high', row.get('pct_from_high', 'N/A'))
            williams_r = row.get('williams_r', row.get('Williams_R', 'N/A'))
            below_sma200 = row.get('pct_below_sma200', row.get('distance_sma200', 'N/A'))
            
            # Format numbers
            if isinstance(rsi, (int, float)):
                rsi = f"{rsi:.1f}"
            if isinstance(pct_off_high, (int, float)):
                pct_off_high = f"{pct_off_high:.1f}%"
            if isinstance(williams_r, (int, float)):
                williams_r = f"{williams_r:.1f}"
            if isinstance(below_sma200, (int, float)):
                below_sma200 = f"{below_sma200:.1f}%"
            if isinstance(price, (int, float)):
                price = f"${price:.2f}"
            
            body += f"""
            <tr style='background: {bg_color};'>
                <td style='padding: 6px; border: 1px solid #ddd; font-weight: bold;'>{symbol}</td>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: center; color: {score_color}; font-weight: bold;'>{score:.1f}</td>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: center;'>{price}</td>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: center;'>{rsi}</td>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: center;'>{pct_off_high}</td>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: center;'>{williams_r}</td>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: center;'>{below_sma200}</td>
            </tr>
            """
        
        body += "</tbody></table>"
        
        # Score legend
        body += """
        <div style='margin-top: 20px; padding: 10px; background: #f5f5f5; border-radius: 4px;'>
            <strong>Score Guide:</strong>
            <span style='margin-left: 15px; color: #1b5e20;'>8-10 = Deeply Oversold</span>
            <span style='margin-left: 15px; color: #2e7d32;'>6-7 = Moderately Oversold</span>
            <span style='margin-left: 15px; color: #f57f17;'>4-5 = Slightly Oversold</span>
        </div>
        """
        
        body += (
            "<hr style='margin-top: 24px; border: none; border-top: 1px solid #eee;'/>"
            "<p style='font-size: 12px; color: #777;'>"
            "Run manually: <code>python oversold.py --all --top 20</code>"
            "</p>"
        )
            
        return body, len(sorted_results)

    def send_email(self, subject: str, html_content: str):
        """Send email via Resend API."""
        if not self.api_key:
            logger.warning("No Resend API Key provided. Skipping email.")
            logger.info(f"Subject: {subject}")
            logger.info("Body preview: " + html_content[:500] + "...")
            return False

        try:
            params = {
                "from": self.from_email,
                "to": self.to_emails,
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            logger.info(f"Email sent! ID: {response.get('id', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def format_subject(self, count: int, top_symbols: List[str] = None, mode: str = "main") -> str:
        """Generate professional email subject line."""
        date_str = datetime.now().strftime("%b %d")
        
        if mode == "reminder":
            return f"Reminder: Oversold Opportunities - {date_str}"
        
        if count == 0:
            return f"Oversold Opportunities: None Found - {date_str}"
        
        if top_symbols and len(top_symbols) > 0:
            symbols_str = ", ".join(top_symbols[:3])
            if len(top_symbols) > 3:
                symbols_str += f" +{len(top_symbols) - 3} more"
            return f"Oversold Opportunities: {symbols_str} - {date_str}"
        
        return f"Oversold Opportunities: {count} Candidates - {date_str}"

