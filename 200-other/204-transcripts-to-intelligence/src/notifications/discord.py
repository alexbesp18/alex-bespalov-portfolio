"""
Discord Notifier

Sends notifications to Discord via webhooks.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

from .base import Notifier, NotificationLevel, NotificationResult

__all__ = ["DiscordNotifier"]

logger = logging.getLogger(__name__)


class DiscordNotifier(Notifier):
    """Sends notifications to Discord.
    
    Requires DISCORD_WEBHOOK_URL environment variable or webhook_url parameter.
    
    Example:
        >>> notifier = DiscordNotifier()
        >>> result = notifier.send_success(
        ...     "Processing complete!",
        ...     title="PodcastAlpha",
        ...     details={"videos": 5, "cost": "$0.50"}
        ... )
    """
    
    channel_name = "discord"
    
    # Emoji for each level
    LEVEL_EMOJI = {
        NotificationLevel.INFO: "ℹ️",
        NotificationLevel.SUCCESS: "✅",
        NotificationLevel.WARNING: "⚠️",
        NotificationLevel.ERROR: "❌",
    }
    
    # Color for each level (Discord embed colors as integers)
    LEVEL_COLOR = {
        NotificationLevel.INFO: 0x3498DB,   # Blue
        NotificationLevel.SUCCESS: 0x2ECC71, # Green
        NotificationLevel.WARNING: 0xF39C12, # Orange
        NotificationLevel.ERROR: 0xE74C3C,   # Red
    }
    
    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Discord notifier.
        
        Args:
            webhook_url: Discord webhook URL. Falls back to DISCORD_WEBHOOK_URL env var.
        """
        self.webhook_url = webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")
    
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
        """Send notification to Discord.
        
        Args:
            message: Main message text.
            level: Notification level (info, success, warning, error).
            title: Optional title for the embed.
            details: Optional key-value pairs to include as fields.
            
        Returns:
            NotificationResult with success status.
        """
        if not self.is_configured():
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                error="Discord webhook URL not configured",
            )
        
        emoji = self.LEVEL_EMOJI.get(level, "")
        color = self.LEVEL_COLOR.get(level, 0x3498DB)
        
        # Build embed
        embed: Dict[str, Any] = {
            "title": f"{emoji} {title}" if title else f"{emoji} Notification",
            "description": message,
            "color": color,
        }
        
        # Add fields if details provided
        if details:
            fields: List[Dict[str, Any]] = []
            for key, value in details.items():
                fields.append({
                    "name": key,
                    "value": str(value),
                    "inline": True,
                })
            embed["fields"] = fields
        
        # Build payload
        payload = {
            "embeds": [embed],
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            
            logger.debug(f"Discord notification sent: {title or 'notification'}")
            
            return NotificationResult(
                success=True,
                channel=self.channel_name,
                response=response.text or "ok",
            )
            
        except requests.RequestException as e:
            error_msg = str(e)
            logger.error(f"Discord notification failed: {error_msg}")
            
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                error=error_msg,
            )

