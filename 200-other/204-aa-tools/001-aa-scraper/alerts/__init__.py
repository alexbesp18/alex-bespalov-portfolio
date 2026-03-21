"""Alerts module for AA Points Monitor."""

from .sender import send_email, send_immediate_alert, send_digest
from .evaluator import evaluate_deals, should_send_alert
from .formatter import format_immediate_alert, format_daily_digest
from .health import HealthMonitor

__all__ = [
    "send_email",
    "send_immediate_alert",
    "send_digest",
    "evaluate_deals",
    "should_send_alert",
    "format_immediate_alert",
    "format_daily_digest",
    "HealthMonitor",
]

