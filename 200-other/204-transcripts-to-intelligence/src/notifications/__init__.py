"""
Notifications Module

Provides notification services for Slack, Discord, and Email.
"""

from .base import Notifier, NotificationResult
from .slack import SlackNotifier
from .discord import DiscordNotifier
from .email import EmailNotifier
from .manager import NotificationManager
from .resend_email import ResendEmailSender, send_video_notification

__all__ = [
    "Notifier",
    "NotificationResult",
    "SlackNotifier",
    "DiscordNotifier",
    "EmailNotifier",
    "NotificationManager",
    "ResendEmailSender",
    "send_video_notification",
]

