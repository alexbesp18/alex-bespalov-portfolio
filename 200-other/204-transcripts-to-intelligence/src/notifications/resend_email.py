"""
Resend Email Notifications for PodcastAlpha.

Sends per-video email notifications with analysis highlights.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

import requests

logger = logging.getLogger(__name__)

# Default configuration - override via env vars
FROM_EMAIL = os.environ.get("SENDER_EMAIL") or os.environ.get("FROM_EMAIL", "")
TO_EMAILS_RAW = os.environ.get("NOTIFICATION_EMAILS") or os.environ.get("TO_EMAILS", "")
TO_EMAILS = [e.strip() for e in TO_EMAILS_RAW.split(",") if e.strip()]


class ResendEmailSender:
    """Send emails via Resend API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: str = FROM_EMAIL,
        to_emails: List[str] = None,
    ):
        self.api_key = api_key or os.environ.get("RESEND_API_KEY")
        self.from_email = from_email
        self.to_emails = to_emails or TO_EMAILS
    
    def send(self, subject: str, html_content: str) -> bool:
        """Send email via Resend API."""
        if not self.api_key:
            logger.warning("No RESEND_API_KEY. Logging email instead.")
            logger.info(f"Subject: {subject}")
            logger.info(f"Preview: {html_content[:300]}...")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
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
                json=payload,
            )
            response.raise_for_status()
            logger.info(f"Email sent via Resend: {response.json().get('id')}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email: {e}")
            return False


def format_video_email(
    video_title: str,
    video_url: str,
    channel: str,
    duration_minutes: float,
    topics_count: int,
    business_ideas: List[Dict[str, Any]],
    consensus_stocks: List[str],
    total_cost: float,
    output_file: str,
) -> str:
    """Format per-video email with highlights."""
    
    date_str = datetime.now().strftime("%b %d, %Y")
    
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1 style="color: #1a1a1a; margin-bottom: 8px; font-size: 20px;">
            New Podcast Analyzed
        </h1>
        <p style="color: #666; margin-top: 0; font-size: 14px;">{date_str}</p>
        
        <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <h2 style="margin: 0 0 8px 0; font-size: 16px; color: #1a1a1a;">
                {video_title}
            </h2>
            <p style="margin: 0; color: #666; font-size: 14px;">
                {channel} &bull; {duration_minutes:.0f} min
            </p>
            <p style="margin: 8px 0 0 0;">
                <a href="{video_url}" style="color: #0066cc; font-size: 13px;">Watch on YouTube →</a>
            </p>
        </div>
        
        <h3 style="color: #333; font-size: 15px; margin-top: 24px; border-bottom: 1px solid #eee; padding-bottom: 8px;">
            Analysis Summary
        </h3>
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
            <tr>
                <td style="padding: 6px 0; color: #666;">Topics Extracted</td>
                <td style="padding: 6px 0; text-align: right; font-weight: 600;">{topics_count}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #666;">Business Ideas</td>
                <td style="padding: 6px 0; text-align: right; font-weight: 600;">{len(business_ideas)}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #666;">Consensus Stock Picks</td>
                <td style="padding: 6px 0; text-align: right; font-weight: 600;">{', '.join(consensus_stocks) if consensus_stocks else 'N/A'}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #666;">Analysis Cost</td>
                <td style="padding: 6px 0; text-align: right; font-weight: 600;">${total_cost:.2f}</td>
            </tr>
        </table>
    """
    
    # Business Ideas Section
    if business_ideas:
        html += """
        <h3 style="color: #333; font-size: 15px; margin-top: 24px; border-bottom: 1px solid #eee; padding-bottom: 8px;">
            Top Business Ideas
        </h3>
        """
        for i, idea in enumerate(business_ideas[:3], 1):
            title = idea.get("title", "Untitled")
            description = idea.get("description", "")[:150]
            target = idea.get("target_market", "")
            
            html += f"""
            <div style="margin: 12px 0; padding: 12px; background: #f8f9fa; border-radius: 6px;">
                <strong style="color: #1a1a1a;">{i}. {title}</strong>
                <p style="color: #555; font-size: 13px; margin: 6px 0;">{description}...</p>
                <p style="color: #888; font-size: 12px; margin: 0;">Target: {target}</p>
            </div>
            """
    
    # Consensus Stocks Section
    if consensus_stocks:
        html += f"""
        <h3 style="color: #333; font-size: 15px; margin-top: 24px; border-bottom: 1px solid #eee; padding-bottom: 8px;">
            Consensus Stock Picks
        </h3>
        <p style="font-size: 14px; color: #555;">
            Stocks mentioned by multiple investor lenses:
        </p>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        """
        for ticker in consensus_stocks[:5]:
            html += f"""
            <span style="background: #e8f5e9; color: #2e7d32; padding: 6px 12px; border-radius: 4px; font-weight: 600; font-size: 13px;">
                ${ticker}
            </span>
            """
        html += "</div>"
    
    # Footer
    html += f"""
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
        <p style="color: #888; font-size: 12px;">
            Full report saved to: <code>{output_file}</code><br>
            <a href="https://github.com/alexbespalov/alex-bespalov-portfolio" style="color: #0066cc;">View in Repository →</a>
        </p>
    </div>
    """
    
    return html


def send_video_notification(
    video_title: str,
    video_url: str,
    channel: str,
    duration_minutes: float,
    topics_count: int,
    business_ideas: List[Dict[str, Any]],
    consensus_stocks: List[str],
    total_cost: float,
    output_file: str,
    api_key: Optional[str] = None,
) -> bool:
    """Send email notification for a processed video."""
    
    # Format subject
    stock_preview = f" | {', '.join(consensus_stocks[:3])}" if consensus_stocks else ""
    subject = f"Podcast Intel: {video_title[:40]}...{stock_preview}"
    
    # Format body
    html = format_video_email(
        video_title=video_title,
        video_url=video_url,
        channel=channel,
        duration_minutes=duration_minutes,
        topics_count=topics_count,
        business_ideas=business_ideas,
        consensus_stocks=consensus_stocks,
        total_cost=total_cost,
        output_file=output_file,
    )
    
    # Send
    sender = ResendEmailSender(api_key=api_key)
    return sender.send(subject, html)

