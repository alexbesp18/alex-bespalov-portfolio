import os
import logging
import resend
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Email configuration - defaults for local dev, override via environment
FROM_EMAIL = os.environ.get("SENDER_EMAIL", "alerts@example.com")
TO_EMAILS = os.environ.get("NOTIFICATION_EMAILS", "").split(",") if os.environ.get("NOTIFICATION_EMAILS") else []


class Notifier:
    def __init__(self, api_key: str, from_email: str = None, to_emails: List[str] = None):
        self.api_key = api_key
        self.from_email = from_email or FROM_EMAIL
        self.to_emails = to_emails or TO_EMAILS
        if api_key:
            resend.api_key = api_key

    def format_email_body(
        self,
        results: List[Dict],
        matrix_data: Optional[List[Dict]] = None,
        mode: str = "main",
        top_20: Optional[List[Dict]] = None,
    ):
        """
        Formats the results into an HTML email body.

        Args:
            results: List of dicts with triggered alerts
            matrix_data: List of dicts with binary matrix flags for each ticker
            mode: "main" or "reminder"
            top_20: List of top 20 tickers by reversal score (for daily leaderboard)

        Returns:
            (html_body, buy_count, sell_count)
        """
        mode = (mode or "main").lower()
        # Separate by category
        buys = []
        sells = []
        upside_reversals = []
        downside_reversals = []
        watches = []
        
        for r in results:
            triggers = r.get('triggers', [])
            trigger_text = ' '.join(triggers).upper()
            
            # Check for reversal signals first
            if 'REV-UP' in trigger_text or 'UPSIDE' in trigger_text:
                upside_reversals.append(r)
            elif 'REV-DN' in trigger_text or 'DOWNSIDE' in trigger_text:
                downside_reversals.append(r)
            elif any(t.startswith("BUY") for t in triggers):
                buys.append(r)
            elif any(t.startswith("SELL") for t in triggers):
                sells.append(r)
            elif triggers:
                watches.append(r)
        
        def format_section(title, items, color):
            if not items:
                return ""
            html = f"<h2 style='color: {color}; border-bottom: 2px solid {color}; padding-bottom: 4px;'>{title}</h2>"
            for item in items:
                symbol = item['symbol']
                theme = item.get('theme', '')
                score = item.get('score', 0)
                price = item.get('price', 0)
                triggers = item.get('triggers', [])
                
                html += f"<div style='margin-bottom: 15px;'>"
                theme_txt = f" ({theme})" if theme else ""
                html += f"<strong>{symbol}{theme_txt}</strong> — Score: {score} | ${price}<br>"
                html += "<ul style='margin-top: 5px;'>"
                for t in triggers:
                   html += f"<li>{t}</li>"
                html += "</ul></div>"
            return html

        body = "<h1 style='margin-bottom: 6px;'>Reversal Candidates</h1>"
        body += f"<p style='margin-top: 0; color: #666;'>Mid-Term Reversal Tracker | {datetime.now().strftime('%Y-%m-%d')}</p>"

        if mode == "reminder":
            body += (
                "<p style='background: #fff8e1; padding: 10px; border: 1px solid #f1e0a6;'>"
                "<strong>Reminder</strong>: these are the alerts from the last main run."
                "</p>"
            )
        else:
            body += (
                "<p style='background: #f5f5f5; padding: 10px; border: 1px solid #ddd;'>"
                "<strong>Noise control</strong>: repeated triggers are suppressed. "
                "This email contains <strong>NEW</strong> signals only."
                "</p>"
            )
        
        # Add trigger-based alerts (HIGH conviction only)
        has_high_conviction = upside_reversals or downside_reversals or buys or sells or watches
        if has_high_conviction:
            body += "<h2 style='color: #B8860B; margin-top: 20px;'>HIGH CONVICTION SIGNALS</h2>"
            body += format_section("UPSIDE REVERSAL", upside_reversals, "#2E8B57")
            body += format_section("DOWNSIDE REVERSAL", downside_reversals, "#CD5C5C")
            body += format_section("BUY", buys, "#228B22")
            body += format_section("SELL", sells, "#B22222")
            body += format_section("WATCH", watches, "#DAA520")
        else:
            body += (
                "<p style='color: #666; font-style: italic;'>"
                "No HIGH conviction signals today (requires score 8+ with divergence and SMA200 support)."
                "</p>"
            )

        # Add Top 20 Leaderboard (always show if available)
        if mode != "reminder" and top_20:
            body += self._format_top_20_table(top_20)

        # Add detailed matrix table for HIGH conviction triggers
        if mode != "reminder" and matrix_data and has_high_conviction:
            # Keep the matrix useful + compact: only include rows for tickers that actually triggered.
            triggered_symbols = {r.get("symbol") for r in results if r.get("symbol")}
            filtered = [row for row in matrix_data if row.get("symbol") in triggered_symbols]
            body += self._format_matrix_table(filtered if filtered else matrix_data)

        body += (
            "<hr style='margin-top: 24px; border: none; border-top: 1px solid #eee;'/>"
            "<p style='font-size: 12px; color: #777;'>"
            "Archive tip: after you execute a trade, suppress that alert for 30 days by running "
            "<code>python reversals.py --archive SYMBOL</code> (or <code>SYMBOL:TRIGGER_KEY</code>)."
            "</p>"
        )
            
        return body, len(buys) + len(upside_reversals), len(sells) + len(downside_reversals)
    
    def _format_matrix_table(self, matrix_data: List[Dict]) -> str:
        """
        Formats matrix data as an HTML table with binary flags.
        """
        if not matrix_data:
            return ""
        
        html = "<h2 style='margin-top: 30px;'>Technical Matrix</h2>"
        html += "<p style='font-size: 12px; color: #666;'>1 = Condition Met | 0 = Not Met | Rev scores shown</p>"
        html += """
        <table style='border-collapse: collapse; font-size: 11px; width: 100%;'>
        <thead>
            <tr style='background: #333; color: white;'>
                <th style='padding: 6px; border: 1px solid #555;'>Symbol</th>
                <th style='padding: 6px; border: 1px solid #555;'>Theme</th>
                <th style='padding: 6px; border: 1px solid #555;'>Score</th>
                <th style='padding: 6px; border: 1px solid #555;' title='Upside Reversal Score'>Rev Up</th>
                <th style='padding: 6px; border: 1px solid #555;' title='Downside Reversal Score'>Rev Dn</th>
                <th style='padding: 6px; border: 1px solid #555;'>Price</th>
                <th style='padding: 6px; border: 1px solid #555;' title='% from 52W High'>%Off</th>
                <th style='padding: 6px; border: 1px solid #555;' title='Above SMA50'>>50</th>
                <th style='padding: 6px; border: 1px solid #555;' title='Above SMA200'>>200</th>
                <th style='padding: 6px; border: 1px solid #555;' title='Golden Cross'>GC</th>
                <th style='padding: 6px; border: 1px solid #555;' title='Death Cross'>DC</th>
                <th style='padding: 6px; border: 1px solid #555;'>RSI</th>
                <th style='padding: 6px; border: 1px solid #555;' title='RSI > 70'>>70</th>
                <th style='padding: 6px; border: 1px solid #555;' title='RSI < 30'><30</th>
            </tr>
        </thead>
        <tbody>
        """
        
        # Sort by score descending
        matrix_data_sorted = sorted(matrix_data, key=lambda x: x.get('score', 0), reverse=True)
        
        for row in matrix_data_sorted:
            # Determine row color based on score
            score = row.get('score', 0)
            if score >= 7:
                bg_color = "#e6ffe6"  # Light green
            elif score <= 4:
                bg_color = "#ffe6e6"  # Light red
            else:
                bg_color = "#fff"
            
            def cell(val, is_binary=True):
                """Format a cell value."""
                if is_binary:
                    color = "#2E8B57" if val == 1 else "#ccc"
                    return f"<td style='padding: 4px; border: 1px solid #ddd; text-align: center; color: {color}; font-weight: bold;'>{val}</td>"
                else:
                    return f"<td style='padding: 4px; border: 1px solid #ddd; text-align: center;'>{val}</td>"
            
            html += f"<tr style='background: {bg_color};'>"
            html += cell(row.get('symbol', ''), False)
            html += cell(row.get('theme', '')[:8], False)  # Truncate theme
            html += cell(row.get('score', 0), False)
            # Reversal scores with color coding
            up_rev = row.get('upside_rev_score', 0)
            dn_rev = row.get('downside_rev_score', 0)
            up_color = '#2E8B57' if up_rev >= 7 else ('#90EE90' if up_rev >= 5 else '#ccc')
            dn_color = '#CD5C5C' if dn_rev >= 7 else ('#F08080' if dn_rev >= 5 else '#ccc')
            html += f"<td style='padding: 4px; border: 1px solid #ddd; text-align: center; color: {up_color}; font-weight: bold;'>{up_rev}</td>"
            html += f"<td style='padding: 4px; border: 1px solid #ddd; text-align: center; color: {dn_color}; font-weight: bold;'>{dn_rev}</td>"
            html += cell(f"${row.get('_price', 0)}", False)
            html += cell(f"{row.get('_pct_from_high', 0)}%", False)
            html += cell(row.get('above_SMA50', 0))
            html += cell(row.get('above_SMA200', 0))
            html += cell(row.get('golden_cross', 0))
            html += cell(row.get('death_cross', 0))
            html += cell(row.get('_rsi', 50), False)
            html += cell(row.get('rsi_above_70', 0))
            html += cell(row.get('rsi_below_30', 0))
            html += "</tr>"
        
        html += "</tbody></table>"
        return html

    def _format_top_20_table(self, top_20: List[Dict]) -> str:
        """
        Formats the top 20 tickers by reversal score as a leaderboard table.
        """
        if not top_20:
            return ""

        html = "<h2 style='margin-top: 30px; color: #2E8B57;'>TOP 20 BY REVERSAL SCORE</h2>"
        html += "<p style='font-size: 12px; color: #666;'>Daily leaderboard sorted by upside reversal score</p>"
        html += """
        <table style='border-collapse: collapse; font-size: 12px; width: 100%;'>
        <thead>
            <tr style='background: #2E8B57; color: white;'>
                <th style='padding: 8px; border: 1px solid #228B22;'>#</th>
                <th style='padding: 8px; border: 1px solid #228B22;'>Symbol</th>
                <th style='padding: 8px; border: 1px solid #228B22;'>Score</th>
                <th style='padding: 8px; border: 1px solid #228B22;'>Conviction</th>
                <th style='padding: 8px; border: 1px solid #228B22;'>Divergence</th>
                <th style='padding: 8px; border: 1px solid #228B22;'>Price</th>
                <th style='padding: 8px; border: 1px solid #228B22;'>RSI</th>
            </tr>
        </thead>
        <tbody>
        """

        for i, row in enumerate(top_20, 1):
            score = row.get('upside_rev_score', 0) or 0
            conviction = row.get('upside_conviction', 'NONE')
            divergence = row.get('divergence_type', 'none')
            price = row.get('close', 0) or row.get('_price', 0)
            rsi = row.get('rsi') or row.get('_rsi', 0)

            # Row color based on score
            if score >= 7:
                bg_color = "#e6ffe6"  # Light green
            elif score >= 5:
                bg_color = "#fffde6"  # Light yellow
            else:
                bg_color = "#fff"

            # Conviction color
            conviction_colors = {
                'HIGH': '#2E8B57',
                'MEDIUM': '#DAA520',
                'LOW': '#999',
                'NONE': '#ccc',
            }
            conv_color = conviction_colors.get(conviction, '#ccc')

            # Divergence indicator
            div_display = divergence if divergence != 'none' else '-'
            div_color = '#2E8B57' if divergence == 'bullish' else ('#CD5C5C' if divergence == 'bearish' else '#999')

            html += f"""
            <tr style='background: {bg_color};'>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: center; font-weight: bold;'>{i}</td>
                <td style='padding: 6px; border: 1px solid #ddd; font-weight: bold;'>{row.get('symbol', '')}</td>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #2E8B57;'>{score:.1f}</td>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: center; color: {conv_color}; font-weight: bold;'>{conviction}</td>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: center; color: {div_color};'>{div_display}</td>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: right;'>${price:.2f}</td>
                <td style='padding: 6px; border: 1px solid #ddd; text-align: center;'>{rsi:.0f}</td>
            </tr>
            """

        html += "</tbody></table>"
        return html

    def send_email(self, subject: str, html_content: str):
        """Send email via Resend API."""
        if not self.api_key:
            logger.warning("No Resend API Key provided. Skipping email.")
            logger.info(f"Subject: {subject}")
            logger.info("Body preview: " + html_content[:500] + "...")
            return False

        try:
            params = {
                "from": self.from_email,
                "to": self.to_emails,
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            logger.info(f"Email sent! ID: {response.get('id', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def format_subject(self, buy_count: int, sell_count: int, mode: str = "main") -> str:
        """Generate professional email subject line."""
        date_str = datetime.now().strftime("%b %d")
        
        if mode == "reminder":
            return f"Reminder: Reversal Candidates - {date_str}"
        
        parts = []
        if buy_count > 0:
            parts.append(f"{buy_count} Upside")
        if sell_count > 0:
            parts.append(f"{sell_count} Downside")
        
        if parts:
            return f"Reversal Candidates: {', '.join(parts)} - {date_str}"
        else:
            return f"Reversal Candidates: No Signals - {date_str}"
