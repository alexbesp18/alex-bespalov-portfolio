"""Notification services for Product Hunt data."""

from src.notifications.email_digest import send_weekly_digest

__all__ = ["send_weekly_digest"]
