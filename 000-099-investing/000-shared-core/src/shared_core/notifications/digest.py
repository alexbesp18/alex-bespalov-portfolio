"""
Daily Digest Email Formatter.

Consolidates results from 008-alerts, 009-reversals, and 010-oversold
into a single daily digest email.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .formatters import COLORS, format_html_table, make_basic_html_email


class DigestFormatter:
    """Formats consolidated daily digest email from all scanner results."""

    @staticmethod
    def format_digest(
        alerts_data: List[Dict[str, Any]],
        reversals_data: List[Dict[str, Any]],
        oversold_data: List[Dict[str, Any]],
        date_str: Optional[str] = None,
    ) -> str:
        """
        Combine all scanner results into single HTML digest.

        Args:
            alerts_data: Results from 008-alerts (signals list)
            reversals_data: Results from 009-reversals (results list)
            oversold_data: Results from 010-oversold (ticker results)
            date_str: Optional date override (YYYY-MM-DD)

        Returns:
            HTML formatted digest body
        """
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d, %Y")

        sections = []

        # Section 1: Trading Signals (008)
        if alerts_data:
            sections.append(DigestFormatter._format_alerts_section(alerts_data))

        # Section 2: Reversal Candidates (009)
        if reversals_data:
            sections.append(DigestFormatter._format_reversals_section(reversals_data))

        # Section 3: Oversold Opportunities (010)
        if oversold_data:
            sections.append(DigestFormatter._format_oversold_section(oversold_data))

        if not sections:
            sections.append('<p style="color: #888;">No signals from any scanner.</p>')

        body_html = "\n".join(sections)

        return make_basic_html_email(
            title=f"Daily Market Digest — {display_date}",
            body_html=body_html,
            footer="Consolidated from Trading Alerts, Reversal Scanner, Oversold Screener",
        )

    @staticmethod
    def _format_alerts_section(signals: List[Dict[str, Any]]) -> str:
        """Format 008-alerts section."""
        buys = [s for s in signals if s.get("action") == "BUY"]
        sells = [s for s in signals if s.get("action") == "SELL"]

        html = [
            '<div style="margin: 24px 0;">',
            f'<h2 style="color: {COLORS["buy"]};">Trading Signals</h2>',
            f'<p style="color: #666;">{len(buys)} BUY, {len(sells)} SELL</p>',
        ]

        if sells:
            html.append(f'<h3 style="color: {COLORS["sell"]};">SELL</h3>')
            for s in sells[:10]:  # Limit to 10
                ticker = s.get("ticker", "?")
                signal = s.get("signal", "").replace("_", " ")
                rsi = s.get("flags", {}).get("rsi", "?")
                price = s.get("flags", {}).get("close", "?")
                html.append(
                    f'<div style="padding: 8px; margin: 4px 0; background: #fff5f5; '
                    f'border-left: 3px solid {COLORS["sell"]};">'
                    f'<strong>{ticker}</strong> — {signal} '
                    f'<span style="color: #666;">(RSI: {rsi}, ${price})</span></div>'
                )

        if buys:
            html.append(f'<h3 style="color: {COLORS["buy"]};">BUY</h3>')
            for s in buys[:10]:
                ticker = s.get("ticker", "?")
                signal = s.get("signal", "").replace("_", " ")
                rsi = s.get("flags", {}).get("rsi", "?")
                price = s.get("flags", {}).get("close", "?")
                html.append(
                    f'<div style="padding: 8px; margin: 4px 0; background: #f5fff5; '
                    f'border-left: 3px solid {COLORS["buy"]};">'
                    f'<strong>{ticker}</strong> — {signal} '
                    f'<span style="color: #666;">(RSI: {rsi}, ${price})</span></div>'
                )

        html.append("</div>")
        return "\n".join(html)

    @staticmethod
    def _format_reversals_section(results: List[Dict[str, Any]]) -> str:
        """Format 009-reversals section."""
        upside = [r for r in results if "UPSIDE" in str(r.get("triggers", []))]
        downside = [r for r in results if "DOWNSIDE" in str(r.get("triggers", []))]

        html = [
            '<div style="margin: 24px 0;">',
            '<h2 style="color: #8e44ad;">Reversal Candidates</h2>',
            f'<p style="color: #666;">{len(upside)} Upside, {len(downside)} Downside</p>',
        ]

        if upside:
            headers = ["Symbol", "Score", "Price", "Triggers"]
            rows = []
            for r in upside[:10]:
                symbol = r.get("symbol", "?")
                score = r.get("score", 0)
                price = r.get("price", 0)
                triggers = ", ".join(r.get("triggers", [])[:2])
                rows.append([symbol, f"{score:.1f}", f"${price:.2f}", triggers])

            html.append('<h3 style="color: #27ae60;">Upside Reversals</h3>')
            html.append(format_html_table(headers, rows))

        if downside:
            headers = ["Symbol", "Score", "Price", "Triggers"]
            rows = []
            for r in downside[:10]:
                symbol = r.get("symbol", "?")
                score = r.get("score", 0)
                price = r.get("price", 0)
                triggers = ", ".join(r.get("triggers", [])[:2])
                rows.append([symbol, f"{score:.1f}", f"${price:.2f}", triggers])

            html.append('<h3 style="color: #e74c3c;">Downside Reversals</h3>')
            html.append(format_html_table(headers, rows))

        html.append("</div>")
        return "\n".join(html)

    @staticmethod
    def _format_oversold_section(results: List[Dict[str, Any]]) -> str:
        """Format 010-oversold section as ranked table."""
        html = [
            '<div style="margin: 24px 0;">',
            '<h2 style="color: #006064;">Oversold Opportunities</h2>',
            f'<p style="color: #666;">Top {len(results)} oversold candidates</p>',
        ]

        if results:
            headers = ["#", "Symbol", "Score", "RSI", "Price"]
            rows = []
            for i, r in enumerate(results[:15], 1):
                ticker = r.get("ticker", r.get("symbol", "?"))
                score = r.get("score", 0)
                rsi = r.get("rsi", 0)
                price = r.get("price", 0)
                rows.append([str(i), ticker, f"{score:.1f}", f"{rsi:.1f}", f"${price:.2f}"])

            html.append(format_html_table(headers, rows))

        html.append("</div>")
        return "\n".join(html)

    @staticmethod
    def format_subject(
        alerts_count: int,
        reversals_count: int,
        oversold_count: int,
    ) -> str:
        """Generate digest email subject line."""
        date_str = datetime.now().strftime("%b %d")
        parts = []

        if alerts_count > 0:
            parts.append(f"{alerts_count} Signals")
        if reversals_count > 0:
            parts.append(f"{reversals_count} Reversals")
        if oversold_count > 0:
            parts.append(f"{oversold_count} Oversold")

        summary = ", ".join(parts) if parts else "No Signals"
        return f"Daily Digest: {summary} — {date_str}"
