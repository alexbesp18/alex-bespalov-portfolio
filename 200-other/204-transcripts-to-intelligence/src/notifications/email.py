"""
Email Notifier

Sends notifications via email using SendGrid or SMTP.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

from .base import Notifier, NotificationLevel, NotificationResult

__all__ = ["EmailNotifier"]

logger = logging.getLogger(__name__)


class EmailNotifier(Notifier):
    """Sends notifications via email.
    
    Supports two modes:
    1. SendGrid API (preferred): Set SENDGRID_API_KEY
    2. SMTP: Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    
    Also requires:
    - NOTIFICATION_EMAIL: Recipient email address
    - FROM_EMAIL: Sender email (defaults to noreply@podcastalpha.local)
    
    Example:
        >>> notifier = EmailNotifier(to_email="user@example.com")
        >>> result = notifier.send_success(
        ...     "5 videos processed successfully",
        ...     title="Processing Complete",
        ...     details={"cost": "$0.50"}
        ... )
    """
    
    channel_name = "email"
    
    # Subject prefix for each level
    LEVEL_PREFIX = {
        NotificationLevel.INFO: "[INFO]",
        NotificationLevel.SUCCESS: "[SUCCESS]",
        NotificationLevel.WARNING: "[WARNING]",
        NotificationLevel.ERROR: "[ERROR]",
    }
    
    def __init__(
        self,
        to_email: Optional[str] = None,
        from_email: Optional[str] = None,
        sendgrid_api_key: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
    ):
        """Initialize email notifier.
        
        Args:
            to_email: Recipient email. Falls back to NOTIFICATION_EMAIL env var.
            from_email: Sender email. Falls back to FROM_EMAIL env var.
            sendgrid_api_key: SendGrid API key. Falls back to SENDGRID_API_KEY env var.
            smtp_host: SMTP host. Falls back to SMTP_HOST env var.
            smtp_port: SMTP port. Falls back to SMTP_PORT env var.
            smtp_user: SMTP username. Falls back to SMTP_USER env var.
            smtp_password: SMTP password. Falls back to SMTP_PASSWORD env var.
        """
        self.to_email = to_email or os.environ.get("NOTIFICATION_EMAIL")
        self.from_email = from_email or os.environ.get("FROM_EMAIL", "noreply@podcastalpha.local")
        
        # SendGrid config
        self.sendgrid_api_key = sendgrid_api_key or os.environ.get("SENDGRID_API_KEY")
        
        # SMTP config
        self.smtp_host = smtp_host or os.environ.get("SMTP_HOST")
        self.smtp_port = smtp_port or int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.environ.get("SMTP_USER")
        self.smtp_password = smtp_password or os.environ.get("SMTP_PASSWORD")
    
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        if not self.to_email:
            return False
        
        # Either SendGrid or SMTP must be configured
        if self.sendgrid_api_key:
            return True
        
        if self.smtp_host and self.smtp_user and self.smtp_password:
            return True
        
        return False
    
    def _build_html(
        self,
        message: str,
        level: NotificationLevel,
        title: Optional[str],
        details: Optional[Dict[str, Any]],
    ) -> str:
        """Build HTML email body."""
        level_colors = {
            NotificationLevel.INFO: "#3498DB",
            NotificationLevel.SUCCESS: "#2ECC71",
            NotificationLevel.WARNING: "#F39C12",
            NotificationLevel.ERROR: "#E74C3C",
        }
        
        color = level_colors.get(level, "#3498DB")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .details {{ margin-top: 20px; }}
                .detail-row {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
                .detail-key {{ font-weight: bold; color: #555; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">{title or 'PodcastAlpha Notification'}</h2>
                </div>
                <div class="content">
                    <p>{message}</p>
        """
        
        if details:
            html += '<div class="details">'
            for key, value in details.items():
                html += f'''
                    <div class="detail-row">
                        <span class="detail-key">{key}:</span> {value}
                    </div>
                '''
            html += '</div>'
        
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_sendgrid(
        self,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> NotificationResult:
        """Send email via SendGrid API."""
        import requests
        
        payload = {
            "personalizations": [{"to": [{"email": self.to_email}]}],
            "from": {"email": self.from_email},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": text_content},
                {"type": "text/html", "value": html_content},
            ],
        }
        
        try:
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.sendgrid_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            response.raise_for_status()
            
            logger.debug(f"Email sent via SendGrid to {self.to_email}")
            
            return NotificationResult(
                success=True,
                channel=self.channel_name,
            )
            
        except requests.RequestException as e:
            error_msg = str(e)
            logger.error(f"SendGrid email failed: {error_msg}")
            
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                error=error_msg,
            )
    
    def _send_smtp(
        self,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> NotificationResult:
        """Send email via SMTP."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = self.to_email
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, self.to_email, msg.as_string())
            
            logger.debug(f"Email sent via SMTP to {self.to_email}")
            
            return NotificationResult(
                success=True,
                channel=self.channel_name,
            )
            
        except smtplib.SMTPException as e:
            error_msg = str(e)
            logger.error(f"SMTP email failed: {error_msg}")
            
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                error=error_msg,
            )
    
    def send(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> NotificationResult:
        """Send email notification.
        
        Args:
            message: Main message text.
            level: Notification level.
            title: Optional title (used in subject and header).
            details: Optional key-value pairs to include.
            
        Returns:
            NotificationResult with success status.
        """
        if not self.is_configured():
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                error="Email not configured (need SendGrid API key or SMTP credentials)",
            )
        
        prefix = self.LEVEL_PREFIX.get(level, "")
        subject = f"{prefix} {title or 'PodcastAlpha Notification'}"
        
        html_content = self._build_html(message, level, title, details)
        
        # Plain text version
        text_content = f"{title or 'Notification'}\n\n{message}"
        if details:
            text_content += "\n\nDetails:\n"
            for key, value in details.items():
                text_content += f"  {key}: {value}\n"
        
        # Try SendGrid first, fall back to SMTP
        if self.sendgrid_api_key:
            return self._send_sendgrid(subject, html_content, text_content)
        else:
            return self._send_smtp(subject, html_content, text_content)

