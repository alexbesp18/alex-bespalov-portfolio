"""
HTML email formatting utilities.

Provides consistent styling for email alerts across all projects.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Default color scheme
COLORS = {
    "buy": "#27ae60",       # Green
    "sell": "#e74c3c",      # Red
    "watch": "#f39c12",     # Orange
    "info": "#3498db",      # Blue
    "header_bg": "#2c3e50", # Dark blue
    "header_text": "#ffffff",
    "row_even": "#f9f9f9",
    "row_odd": "#ffffff",
    "border": "#e1e1e1",
}


def format_html_table(
    headers: List[str],
    rows: List[List[Any]],
    style: Optional[Dict[str, str]] = None,
) -> str:
    """
    Create an HTML table with consistent styling.

    Args:
        headers: List of column header strings
        rows: List of row data (each row is a list of cell values)
        style: Optional style overrides

    Returns:
        HTML table string

    Example:
        >>> html = format_html_table(
        ...     ["Ticker", "Action", "Score"],
        ...     [["NVDA", "BUY", 8.5], ["AAPL", "HOLD", 6.0]]
        ... )
    """
    s = style or COLORS

    html_parts = [
        '<table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;">',
        '<thead>',
        f'<tr style="background-color: {s.get("header_bg", COLORS["header_bg"])};">',
    ]

    for header in headers:
        html_parts.append(
            f'<th style="padding: 12px; text-align: left; color: {s.get("header_text", COLORS["header_text"])}; '
            f'border-bottom: 2px solid {s.get("border", COLORS["border"])};">{header}</th>'
        )

    html_parts.extend(['</tr>', '</thead>', '<tbody>'])

    for i, row in enumerate(rows):
        bg_color = s.get("row_even", COLORS["row_even"]) if i % 2 == 0 else s.get("row_odd", COLORS["row_odd"])
        html_parts.append(f'<tr style="background-color: {bg_color};">')

        for cell in row:
            html_parts.append(
                f'<td style="padding: 10px; border-bottom: 1px solid {s.get("border", COLORS["border"])};">'
                f'{cell}</td>'
            )

        html_parts.append('</tr>')

    html_parts.extend(['</tbody>', '</table>'])

    return ''.join(html_parts)


def format_html_section(
    title: str,
    items: List[str],
    color: str = "info",
) -> str:
    """
    Create a styled HTML section with a header and list of items.

    Args:
        title: Section title
        items: List of items to display
        color: Color key from COLORS dict (buy, sell, watch, info)

    Returns:
        HTML section string
    """
    c = COLORS.get(color, COLORS["info"])

    html_parts = [
        '<div style="margin: 20px 0;">',
        f'<h3 style="color: {c}; border-bottom: 2px solid {c}; padding-bottom: 5px;">{title}</h3>',
        '<ul style="padding-left: 20px;">',
    ]

    for item in items:
        html_parts.append(f'<li style="margin: 8px 0;">{item}</li>')

    html_parts.extend(['</ul>', '</div>'])

    return ''.join(html_parts)


def format_html_list(
    items: List[Dict[str, Any]],
    format_func: Optional["Callable[[Dict[str, Any]], str]"] = None,
) -> str:
    """
    Format a list of items as HTML.

    Args:
        items: List of item dicts
        format_func: Optional function to format each item.
                     If None, uses str(item).

    Returns:
        HTML unordered list
    """
    html_parts = ['<ul style="padding-left: 20px;">']

    for item in items:
        text = format_func(item) if format_func else str(item)
        html_parts.append(f'<li style="margin: 8px 0;">{text}</li>')

    html_parts.append('</ul>')

    return ''.join(html_parts)


def format_action_link(
    ticker: str,
    action: str,
    base_url: Optional[str] = None,
    action_type: str = "issue",
) -> str:
    """
    Create an action link for a signal.

    Creates a link to create a GitHub issue or perform another action.

    Args:
        ticker: Stock symbol
        action: Action type (BUY, SELL, etc.)
        base_url: Base URL for the action endpoint
        action_type: Type of action link to create

    Returns:
        HTML anchor link
    """
    if not base_url:
        # Default to no link
        return f"{ticker} - {action}"

    url = f"{base_url}?ticker={ticker}&action={action}"
    return f'<a href="{url}" style="color: {COLORS.get(action.lower(), COLORS["info"])}; text-decoration: none;">{ticker} - {action}</a>'


def format_subject(
    signals: List[Dict[str, Any]],
    mode: str = "alert",
    date: Optional[datetime] = None,
) -> str:
    """
    Generate email subject line from signals.

    Args:
        signals: List of signal dicts with 'action' key
        mode: Email mode ("alert", "reminder", "digest")
        date: Date for subject (defaults to today)

    Returns:
        Email subject string

    Example:
        >>> format_subject([{"action": "BUY"}, {"action": "SELL"}], "alert")
        "📊 Trading Alert: 1 BUY, 1 SELL (Dec 21)"
    """
    if date is None:
        date = datetime.now()

    date_str = date.strftime("%b %d")

    buy_count = sum(1 for s in signals if s.get("action", "").upper() == "BUY")
    sell_count = sum(1 for s in signals if s.get("action", "").upper() == "SELL")

    parts = []
    if buy_count:
        parts.append(f"{buy_count} BUY")
    if sell_count:
        parts.append(f"{sell_count} SELL")

    counts = ", ".join(parts) if parts else "No signals"

    prefix = {
        "alert": "📊 Trading Alert",
        "reminder": "⏰ Trading Reminder",
        "digest": "📋 Daily Digest",
    }.get(mode, "📊 Alert")

    return f"{prefix}: {counts} ({date_str})"


def make_basic_html_email(
    title: str,
    body_html: str,
    footer: Optional[str] = None,
) -> str:
    """
    Wrap content in a basic HTML email template.

    Args:
        title: Email title (shown in header)
        body_html: Main HTML content
        footer: Optional footer text

    Returns:
        Complete HTML document
    """
    footer_html = f'<p style="color: #888; font-size: 12px; margin-top: 30px;">{footer}</p>' if footer else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
        <h1 style="color: {COLORS['header_bg']}; border-bottom: 3px solid {COLORS['header_bg']}; padding-bottom: 10px;">
            {title}
        </h1>
        {body_html}
        {footer_html}
    </body>
    </html>
    """

