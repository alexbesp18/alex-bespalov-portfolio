"""
Base Notifier

Abstract base class for all notification channels.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class NotificationLevel(str, Enum):
    """Notification priority/type."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class NotificationResult:
    """Result of a notification attempt.
    
    Attributes:
        success: Whether the notification was sent successfully.
        channel: The notification channel (slack, discord, email).
        error: Error message if failed.
        response: Raw response from the service.
    """
    success: bool
    channel: str
    error: Optional[str] = None
    response: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "channel": self.channel,
            "error": self.error,
        }


class Notifier(ABC):
    """Abstract base class for notification channels.
    
    All notifiers must implement the send method.
    """
    
    channel_name: str = "base"
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the notifier is properly configured.
        
        Returns:
            True if all required credentials/config are available.
        """
        pass
    
    @abstractmethod
    def send(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> NotificationResult:
        """Send a notification.
        
        Args:
            message: Main notification message.
            level: Notification priority/type.
            title: Optional title/header.
            details: Optional additional data to include.
            
        Returns:
            NotificationResult indicating success/failure.
        """
        pass
    
    def send_success(
        self,
        message: str,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> NotificationResult:
        """Convenience method for success notifications."""
        return self.send(message, NotificationLevel.SUCCESS, title, details)
    
    def send_error(
        self,
        message: str,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> NotificationResult:
        """Convenience method for error notifications."""
        return self.send(message, NotificationLevel.ERROR, title, details)
    
    def send_warning(
        self,
        message: str,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> NotificationResult:
        """Convenience method for warning notifications."""
        return self.send(message, NotificationLevel.WARNING, title, details)

