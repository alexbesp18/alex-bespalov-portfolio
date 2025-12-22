"""
Resend email client for sending notifications.

Uses the Resend API (resend.com) for email delivery.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """
    Email configuration.
    
    Attributes:
        api_key: Resend API key
        from_address: Sender email address
        to_addresses: List of recipient email addresses
        reply_to: Optional reply-to address
    """
    api_key: str
    from_address: str
    to_addresses: List[str]
    reply_to: Optional[str] = None

    @classmethod
    def from_env(cls) -> Optional["EmailConfig"]:
        """
        Create config from environment variables.
        
        Environment variables:
        - RESEND_API_KEY
        - EMAIL_FROM
        - EMAIL_TO (comma-separated)
        - EMAIL_REPLY_TO (optional)
        """
        api_key = os.getenv("RESEND_API_KEY")
        from_addr = os.getenv("EMAIL_FROM")
        to_addr = os.getenv("EMAIL_TO")

        if not all([api_key, from_addr, to_addr]):
            return None

        # Type narrowing for mypy
        assert api_key is not None
        assert from_addr is not None
        assert to_addr is not None

        return cls(
            api_key=api_key,
            from_address=from_addr,
            to_addresses=[a.strip() for a in to_addr.split(",")],
            reply_to=os.getenv("EMAIL_REPLY_TO"),
        )


class ResendEmailClient:
    """
    Email client using Resend API.
    
    Supports both new and legacy Resend library versions.
    
    Example:
        >>> config = EmailConfig.from_env()
        >>> client = ResendEmailClient(config)
        >>> client.send(
        ...     subject="Test Alert",
        ...     html="<h1>Hello</h1>",
        ... )
    """

    def __init__(self, config: EmailConfig):
        """
        Initialize with email configuration.
        
        Args:
            config: EmailConfig with API key and addresses
        """
        self.config = config
        self._initialized = False
        self._resend = None

    def _ensure_initialized(self):
        """Lazy initialize Resend client."""
        if self._initialized:
            return

        try:
            import resend
            resend.api_key = self.config.api_key
            self._resend = resend
            self._initialized = True
        except ImportError:
            logger.error("Resend library not installed. Run: pip install resend")
            raise

    def send(
        self,
        subject: str,
        html: str,
        to: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> bool:
        """
        Send an email.
        
        Args:
            subject: Email subject line
            html: HTML body content
            to: Recipient list (defaults to config.to_addresses)
            dry_run: If True, log but don't send
            
        Returns:
            True if email sent successfully
        """
        recipients = to or self.config.to_addresses

        if dry_run:
            logger.info(f"[DRY RUN] Would send email: {subject}")
            logger.debug(f"To: {recipients}")
            return True

        self._ensure_initialized()

        try:
            params: Dict[str, Any] = {
                "from": self.config.from_address,
                "to": recipients,
                "subject": subject,
                "html": html,
            }

            if self.config.reply_to:
                params["reply_to"] = self.config.reply_to

            # Try new API (resend >= 0.6.0)
            if self._resend is None:
                raise RuntimeError("Resend client not initialized")
            try:
                self._resend.Emails.send(params)  # type: ignore[union-attr]
            except AttributeError:
                # Fall back to legacy API
                self._resend.Emails.SendParams(**params)  # type: ignore[union-attr]

            logger.info(f"Email sent: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_plain(
        self,
        subject: str,
        text: str,
        to: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> bool:
        """
        Send a plain text email.
        
        Args:
            subject: Email subject line
            text: Plain text body
            to: Recipient list
            dry_run: If True, log but don't send
            
        Returns:
            True if email sent successfully
        """
        # Convert plain text to simple HTML
        html = f"<pre style='font-family: monospace;'>{text}</pre>"
        return self.send(subject, html, to, dry_run)


def make_resend_client_from_env() -> Optional[ResendEmailClient]:
    """
    Create a ResendEmailClient from environment variables.
    
    Returns:
        ResendEmailClient if configured, None otherwise
    """
    config = EmailConfig.from_env()
    if not config:
        logger.warning("Email not configured. Set RESEND_API_KEY, EMAIL_FROM, EMAIL_TO")
        return None
    return ResendEmailClient(config)

