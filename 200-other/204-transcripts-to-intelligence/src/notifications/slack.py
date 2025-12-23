"""
Slack Notifier

Sends notifications to Slack via webhooks.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

from .base import Notifier, NotificationLevel, NotificationResult

__all__ = ["SlackNotifier"]

logger = logging.getLogger(__name__)


class SlackNotifier(Notifier):
    """Sends notifications to Slack.
    
    Requires SLACK_WEBHOOK_URL environment variable or webhook_url parameter.
    
    Example:
        >>> notifier = SlackNotifier()
        >>> result = notifier.send_success(
        ...     "Processing complete!",
        ...     title="PodcastAlpha",
        ...     details={"videos": 5, "cost": "$0.50"}
        ... )
    """
    
    channel_name = "slack"
    
    # Emoji for each level
    LEVEL_EMOJI = {
        NotificationLevel.INFO: "ℹ️",
        NotificationLevel.SUCCESS: "✅",
        NotificationLevel.WARNING: "⚠️",
        NotificationLevel.ERROR: "❌",
    }
    
    # Color for each level (Slack attachment colors)
    LEVEL_COLOR = {
        NotificationLevel.INFO: "#36a64f",
        NotificationLevel.SUCCESS: "#2eb886",
        NotificationLevel.WARNING: "#daa038",
        NotificationLevel.ERROR: "#a30200",
    }
    
    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL. Falls back to SLACK_WEBHOOK_URL env var.
        """
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    
    def is_configured(self) -> bool:
        """Check if webhook URL is available."""
        return bool(self.webhook_url)
    
    def send(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> NotificationResult:
        """Send notification to Slack.
        
        Args:
            message: Main message text.
            level: Notification level (info, success, warning, error).
            title: Optional title for the message.
            details: Optional key-value pairs to include.
            
        Returns:
            NotificationResult with success status.
        """
        if not self.is_configured():
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                error="Slack webhook URL not configured",
            )
        
        emoji = self.LEVEL_EMOJI.get(level, "")
        color = self.LEVEL_COLOR.get(level, "#36a64f")
        
        # Build blocks
        blocks: List[Dict[str, Any]] = []
        
        # Header with emoji
        header_text = f"{emoji} {title}" if title else f"{emoji} Notification"
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{header_text}*\n{message}",
            },
        })
        
        # Add details as fields if provided
        if details:
            fields = []
            for key, value in details.items():
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:*\n{value}",
                })
            
            # Slack allows max 10 fields per section
            for i in range(0, len(fields), 10):
                blocks.append({
                    "type": "section",
                    "fields": fields[i:i + 10],
                })
        
        # Build payload
        payload = {
            "blocks": blocks,
            "attachments": [{"color": color, "blocks": []}],
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            
            logger.debug(f"Slack notification sent: {title or 'notification'}")
            
            return NotificationResult(
                success=True,
                channel=self.channel_name,
                response=response.text,
            )
            
        except requests.RequestException as e:
            error_msg = str(e)
            logger.error(f"Slack notification failed: {error_msg}")
            
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                error=error_msg,
            )

