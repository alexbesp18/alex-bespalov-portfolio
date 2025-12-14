import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self, api_key, from_email, to_email):
        self.api_key = api_key
        self.from_email = from_email
        self.to_email = to_email

    def format_email_body(self, results: List[Dict], matrix_data: Optional[List[Dict]] = None, mode: str = "main"):
        """
        Formats the results into an HTML email body.
        
        Args:
            results: List of dicts with triggered alerts
            matrix_data: List of dicts with binary matrix flags for each ticker
        
        Returns:
            (html_body, buy_count, sell_count)
        """
        mode = (mode or "main").lower()
        # Separate by category
        buys = []
        sells = []
        watches = []
        
        for r in results:
            triggers = r.get('triggers', [])
            if any(t.startswith("BUY") for t in triggers):
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

        body = "<h1 style='margin-bottom: 6px;'>SENTINEL</h1>"
        body += f"<p style='margin-top: 0; color: #666;'>Date: {datetime.now().strftime('%Y-%m-%d')}</p>"

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
        
        # Add trigger-based alerts
        if buys or sells or watches:
            body += format_section("BUY", buys, "#2E8B57")
            body += format_section("SELL", sells, "#CD5C5C")
            body += format_section("WATCH", watches, "#DAA520")
        
        # Add matrix table
        if mode != "reminder" and matrix_data and (buys or sells or watches):
            # Keep the matrix useful + compact: only include rows for tickers that actually triggered.
            triggered_symbols = {r.get("symbol") for r in results if r.get("symbol")}
            filtered = [row for row in matrix_data if row.get("symbol") in triggered_symbols]
            body += self._format_matrix_table(filtered if filtered else matrix_data)
        elif not results:
            body += "<p>No triggers found today.</p>"

        body += (
            "<hr style='margin-top: 24px; border: none; border-top: 1px solid #eee;'/>"
            "<p style='font-size: 12px; color: #777;'>"
            "Archive tip: after you execute a trade, suppress that alert for 30 days by running "
            "<code>python sentinel/sentinel.py --archive SYMBOL</code> (or <code>SYMBOL:TRIGGER_KEY</code>). "
            "Email-reply auto-archive can be added later via SendGrid Inbound Parse."
            "</p>"
        )
            
        return body, len(buys), len(sells)
    
    def _format_matrix_table(self, matrix_data: List[Dict]) -> str:
        """
        Formats matrix data as an HTML table with binary flags.
        """
        if not matrix_data:
            return ""
        
        html = "<h2 style='margin-top: 30px;'>Technical Matrix</h2>"
        html += "<p style='font-size: 12px; color: #666;'>1 = Condition Met | 0 = Not Met</p>"
        html += """
        <table style='border-collapse: collapse; font-size: 11px; width: 100%;'>
        <thead>
            <tr style='background: #333; color: white;'>
                <th style='padding: 6px; border: 1px solid #555;'>Symbol</th>
                <th style='padding: 6px; border: 1px solid #555;'>Theme</th>
                <th style='padding: 6px; border: 1px solid #555;'>Score</th>
                <th style='padding: 6px; border: 1px solid #555;'>Price</th>
                <th style='padding: 6px; border: 1px solid #555;' title='% from 52W High'>%Off</th>
                <th style='padding: 6px; border: 1px solid #555;' title='-5%'>-5</th>
                <th style='padding: 6px; border: 1px solid #555;' title='-10%'>-10</th>
                <th style='padding: 6px; border: 1px solid #555;' title='-15%'>-15</th>
                <th style='padding: 6px; border: 1px solid #555;' title='-20%'>-20</th>
                <th style='padding: 6px; border: 1px solid #555;' title='-30%'>-30</th>
                <th style='padding: 6px; border: 1px solid #555;' title='Above SMA5'>>5</th>
                <th style='padding: 6px; border: 1px solid #555;' title='Above SMA14'>>14</th>
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
            html += cell(f"${row.get('_price', 0)}", False)
            html += cell(f"{row.get('_pct_from_high', 0)}%", False)
            html += cell(row.get('corr_5pct', 0))
            html += cell(row.get('corr_10pct', 0))
            html += cell(row.get('corr_15pct', 0))
            html += cell(row.get('corr_20pct', 0))
            html += cell(row.get('corr_30pct', 0))
            html += cell(row.get('above_SMA5', 0))
            html += cell(row.get('above_SMA14', 0))
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

    def send_email(self, subject, html_content):
        if not self.api_key:
            logger.warning("No SendGrid API Key provided. Skipping email.")
            logger.info(f"Subject: {subject}")
            logger.info("Body preview: " + html_content[:500] + "...")
            return

        message = Mail(
            from_email=self.from_email,
            to_emails=self.to_email,
            subject=subject,
            html_content=html_content)
        
        try:
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            logger.info(f"Email sent! Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
