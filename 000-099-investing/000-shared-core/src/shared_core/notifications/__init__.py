"""
Email notification utilities via Resend.

Provides:
- ResendEmailClient: Send emails via Resend API
- HTML formatting utilities
- Template helpers
"""

from .formatters import (
    format_action_link,
    format_html_list,
    format_html_section,
    format_html_table,
    format_subject,
    make_basic_html_email,
)
from .resend_client import EmailConfig, ResendEmailClient

__all__ = [
    # Client
    "ResendEmailClient",
    "EmailConfig",
    # Formatters
    "format_html_table",
    "format_html_section",
    "format_html_list",
    "format_action_link",
    "format_subject",
    "make_basic_html_email",
]

