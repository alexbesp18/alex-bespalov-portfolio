"""
Notification Manager

Orchestrates sending notifications across multiple channels.
"""

import logging
from typing import Any, Dict, List, Optional

from .base import Notifier, NotificationLevel, NotificationResult
from .slack import SlackNotifier
from .discord import DiscordNotifier
from .email import EmailNotifier

__all__ = ["NotificationManager"]

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages notifications across multiple channels.
    
    Automatically detects which channels are configured and sends
    notifications to all of them.
    
    Example:
        >>> manager = NotificationManager()
        >>> results = manager.notify_all(
        ...     "Processing complete!",
        ...     level=NotificationLevel.SUCCESS,
        ...     title="PodcastAlpha",
        ...     details={"videos": 5, "cost": "$0.50"}
        ... )
        >>> for result in results:
        ...     print(f"{result.channel}: {'✅' if result.success else '❌'}")
    """
    
    def __init__(
        self,
        slack: Optional[SlackNotifier] = None,
        discord: Optional[DiscordNotifier] = None,
        email: Optional[EmailNotifier] = None,
        auto_configure: bool = True,
    ):
        """Initialize notification manager.
        
        Args:
            slack: Pre-configured Slack notifier.
            discord: Pre-configured Discord notifier.
            email: Pre-configured Email notifier.
            auto_configure: If True, automatically create notifiers from env vars.
        """
        self.notifiers: List[Notifier] = []
        
        if auto_configure:
            # Auto-configure from environment
            slack_notifier = slack or SlackNotifier()
            if slack_notifier.is_configured():
                self.notifiers.append(slack_notifier)
            
            discord_notifier = discord or DiscordNotifier()
            if discord_notifier.is_configured():
                self.notifiers.append(discord_notifier)
            
            email_notifier = email or EmailNotifier()
            if email_notifier.is_configured():
                self.notifiers.append(email_notifier)
        else:
            # Only use explicitly provided notifiers
            if slack:
                self.notifiers.append(slack)
            if discord:
                self.notifiers.append(discord)
            if email:
                self.notifiers.append(email)
    
    @property
    def configured_channels(self) -> List[str]:
        """Get list of configured channel names."""
        return [n.channel_name for n in self.notifiers]
    
    def has_channels(self) -> bool:
        """Check if any notification channels are configured."""
        return len(self.notifiers) > 0
    
    def notify_all(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,
    ) -> List[NotificationResult]:
        """Send notification to all configured channels.
        
        Args:
            message: Main message text.
            level: Notification level.
            title: Optional title.
            details: Optional key-value pairs.
            channels: Optional list of specific channels to use.
            
        Returns:
            List of NotificationResult, one per channel.
        """
        results = []
        
        for notifier in self.notifiers:
            # Skip if specific channels requested and this isn't one
            if channels and notifier.channel_name not in channels:
                continue
            
            try:
                result = notifier.send(message, level, title, details)
                results.append(result)
            except Exception as e:
                logger.error(f"Notification failed for {notifier.channel_name}: {e}")
                results.append(NotificationResult(
                    success=False,
                    channel=notifier.channel_name,
                    error=str(e),
                ))
        
        return results
    
    def notify_success(
        self,
        message: str,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,
    ) -> List[NotificationResult]:
        """Send success notification to all channels."""
        return self.notify_all(message, NotificationLevel.SUCCESS, title, details, channels)
    
    def notify_error(
        self,
        message: str,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,
    ) -> List[NotificationResult]:
        """Send error notification to all channels."""
        return self.notify_all(message, NotificationLevel.ERROR, title, details, channels)
    
    def notify_warning(
        self,
        message: str,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,
    ) -> List[NotificationResult]:
        """Send warning notification to all channels."""
        return self.notify_all(message, NotificationLevel.WARNING, title, details, channels)
    
    # Convenience methods for common notifications
    
    def notify_processing_complete(
        self,
        videos_processed: int,
        total_cost: float,
        errors: int = 0,
        output_dir: Optional[str] = None,
    ) -> List[NotificationResult]:
        """Send standard processing complete notification."""
        if errors > 0:
            level = NotificationLevel.WARNING
            title = "PodcastAlpha: Processing Complete (with errors)"
        else:
            level = NotificationLevel.SUCCESS
            title = "PodcastAlpha: Processing Complete"
        
        message = f"{videos_processed} video(s) processed successfully."
        if errors > 0:
            message += f" {errors} video(s) failed."
        
        details = {
            "Videos Processed": videos_processed,
            "Total Cost": f"${total_cost:.4f}",
        }
        
        if errors > 0:
            details["Errors"] = errors
        
        if output_dir:
            details["Output Directory"] = output_dir
        
        return self.notify_all(message, level, title, details)
    
    def notify_processing_failed(
        self,
        error: str,
        video_url: Optional[str] = None,
    ) -> List[NotificationResult]:
        """Send processing failed notification."""
        title = "PodcastAlpha: Processing Failed"
        message = f"Video processing failed: {error}"
        
        details = {"Error": error}
        if video_url:
            details["Video URL"] = video_url
        
        return self.notify_all(message, NotificationLevel.ERROR, title, details)

