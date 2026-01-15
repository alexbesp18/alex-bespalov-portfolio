"""
Email notification utilities via Resend.

Provides:
- ResendEmailClient: Send emails via Resend API
- DigestFormatter: Consolidated daily digest formatting
- HTML formatting utilities
- Template helpers
"""

from .digest import DigestFormatter
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
    # Digest
    "DigestFormatter",
    # Formatters
    "format_html_table",
    "format_html_section",
    "format_html_list",
    "format_action_link",
    "format_subject",
    "make_basic_html_email",
]

