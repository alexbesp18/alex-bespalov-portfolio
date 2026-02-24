"""True Value Notifier — dark-theme HTML email for True Value report."""

import os
import logging
import resend
from datetime import datetime
from typing import List

from .true_value_models import TrueValueResult, Tier

logger = logging.getLogger(__name__)

FROM_EMAIL = os.environ.get("SENDER_EMAIL", "alerts@example.com")
TO_EMAILS = (
    os.environ.get("NOTIFICATION_EMAILS", "").split(",")
    if os.environ.get("NOTIFICATION_EMAILS")
    else []
)

# Tier colors
TIER_COLORS = {
    Tier.STRUCTURAL_BUY: "#00C853",
    Tier.WATCHLIST_ENTRY: "#FFB300",
    Tier.REVERSAL_SPECULATIVE: "#9E9E9E",
}

TIER_BG = {
    Tier.STRUCTURAL_BUY: "rgba(0,200,83,0.12)",
    Tier.WATCHLIST_ENTRY: "rgba(255,179,0,0.12)",
    Tier.REVERSAL_SPECULATIVE: "rgba(158,158,158,0.10)",
}


class TrueValueNotifier:
    """Formats and sends True Value Oversold email reports."""

    def __init__(
        self,
        api_key: str,
        from_email: str = None,
        to_emails: List[str] = None,
    ):
        self.api_key = api_key
        self.from_email = from_email or FROM_EMAIL
        self.to_emails = to_emails or TO_EMAILS
        if api_key:
            resend.api_key = api_key

    def format_email_body(
        self, results: List[TrueValueResult], total_scanned: int
    ) -> tuple:
        """Generate dark-theme HTML email body.

        Returns:
            (html_body, count_of_results)
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        passed = len(results)

        body = f"""
<div style="background:#1a1a2e;color:#e0e0e0;font-family:Arial,Helvetica,sans-serif;padding:24px;max-width:720px;margin:0 auto;">
  <h1 style="color:#e0e0e0;margin-bottom:4px;font-size:22px;">True Value Oversold</h1>
  <p style="color:#888;margin-top:0;font-size:13px;">Structural integrity filter | {date_str}</p>
  <p style="background:#0f3460;padding:10px 14px;border-radius:4px;font-size:13px;color:#b0bec5;">
    Oversold names that pass the <strong style="color:#e0e0e0;">structural gate</strong>:
    MT RSI &lt; 35, at least one integrity path, and not in terminal decline.
  </p>
"""

        if not results:
            body += """
  <div style="background:#16213e;padding:20px;border-radius:6px;margin:20px 0;text-align:center;">
    <p style="color:#9E9E9E;font-size:14px;">No names passed the True Value gate today.</p>
    <p style="color:#666;font-size:12px;">Market either not oversold or oversold names lack structural integrity.</p>
  </div>
"""
        else:
            body += self._build_table(results)

        # Footer
        body += f"""
  <div style="margin-top:24px;padding:12px;background:#0f3460;border-radius:4px;font-size:11px;color:#888;">
    <strong style="color:#b0bec5;">Gate criteria:</strong>
    MT RSI &lt; 35 &bull;
    Structural path (SMA BULLISH + LT&ge;5, or OBV ACCUM + LT&ge;4, or LT&ge;7, or SMA BULLISH + OBV ACCUM) &bull;
    Not terminal (STRONG_DOWNTREND + BEARISH + DISTRIBUTING)
    <br/>
    <span style="margin-top:6px;display:inline-block;">
      Scanned: {total_scanned} tickers | Passed Gate: {passed} | {date_str}
    </span>
  </div>
</div>
"""
        return body, passed

    def _build_table(self, results: List[TrueValueResult]) -> str:
        """Build the HTML table rows."""
        html = """
  <table style="border-collapse:collapse;font-size:12px;width:100%;margin-top:16px;">
    <thead>
      <tr style="background:#0f3460;">
        <th style="padding:8px 6px;border-bottom:2px solid #1a1a2e;color:#b0bec5;text-align:left;">Symbol</th>
        <th style="padding:8px 6px;border-bottom:2px solid #1a1a2e;color:#b0bec5;text-align:center;">TV Score</th>
        <th style="padding:8px 6px;border-bottom:2px solid #1a1a2e;color:#b0bec5;text-align:center;">Price</th>
        <th style="padding:8px 6px;border-bottom:2px solid #1a1a2e;color:#b0bec5;text-align:center;">MT RSI</th>
        <th style="padding:8px 6px;border-bottom:2px solid #1a1a2e;color:#b0bec5;text-align:center;">LT Score</th>
        <th style="padding:8px 6px;border-bottom:2px solid #1a1a2e;color:#b0bec5;text-align:center;">SMA Align</th>
        <th style="padding:8px 6px;border-bottom:2px solid #1a1a2e;color:#b0bec5;text-align:center;">OBV</th>
        <th style="padding:8px 6px;border-bottom:2px solid #1a1a2e;color:#b0bec5;text-align:center;">1M%</th>
        <th style="padding:8px 6px;border-bottom:2px solid #1a1a2e;color:#b0bec5;text-align:center;">1Y%</th>
      </tr>
    </thead>
    <tbody>
"""
        for r in results:
            accent = TIER_COLORS.get(r.tier, "#9E9E9E")
            score_bg = TIER_BG.get(r.tier, "transparent")
            pct_1m_color = "#66BB6A" if r.pct_1m >= 0 else "#EF5350"
            pct_1y_color = "#66BB6A" if r.pct_1y >= 0 else "#EF5350"
            pct_1m_str = f"{r.pct_1m:+.1f}%"
            pct_1y_str = f"{r.pct_1y:+.1f}%" if r.pct_1y != 0.0 else "N/A"

            sma_display = r.sma_alignment.replace("_", " ").title()
            obv_display = r.obv_trend.replace("_", " ").title()

            html += f"""
      <tr style="background:#16213e;border-left:3px solid {accent};">
        <td style="padding:7px 6px;border-bottom:1px solid #1a1a2e;font-weight:bold;color:#e0e0e0;">{r.ticker}</td>
        <td style="padding:7px 6px;border-bottom:1px solid #1a1a2e;text-align:center;font-weight:bold;color:{accent};background:{score_bg};">{r.true_value_score:.1f}</td>
        <td style="padding:7px 6px;border-bottom:1px solid #1a1a2e;text-align:center;color:#e0e0e0;">${r.price:.2f}</td>
        <td style="padding:7px 6px;border-bottom:1px solid #1a1a2e;text-align:center;color:#EF5350;">{r.mt_rsi:.1f}</td>
        <td style="padding:7px 6px;border-bottom:1px solid #1a1a2e;text-align:center;color:#e0e0e0;">{r.lt_score:.1f}</td>
        <td style="padding:7px 6px;border-bottom:1px solid #1a1a2e;text-align:center;color:#b0bec5;font-size:11px;">{sma_display}</td>
        <td style="padding:7px 6px;border-bottom:1px solid #1a1a2e;text-align:center;color:#b0bec5;font-size:11px;">{obv_display}</td>
        <td style="padding:7px 6px;border-bottom:1px solid #1a1a2e;text-align:center;color:{pct_1m_color};">{pct_1m_str}</td>
        <td style="padding:7px 6px;border-bottom:1px solid #1a1a2e;text-align:center;color:{pct_1y_color};">{pct_1y_str}</td>
      </tr>
"""
        html += "    </tbody>\n  </table>\n"

        # Tier legend
        html += """
  <div style="margin-top:12px;font-size:11px;color:#888;">
    <span style="color:#00C853;">&bull; Structural Buy (&ge;7.0)</span> &nbsp;
    <span style="color:#FFB300;">&bull; Watchlist Entry (&ge;5.5)</span> &nbsp;
    <span style="color:#9E9E9E;">&bull; Reversal Speculative (&ge;4.0)</span>
  </div>
"""
        return html

    def format_subject(self, count: int, top_tickers: List[str]) -> str:
        """Generate email subject line."""
        date_str = datetime.now().strftime("%b %d")

        if count == 0:
            return f"True Value Oversold: None Today \u2014 {date_str}"

        if top_tickers:
            symbols = ", ".join(top_tickers[:3])
            return f"True Value Oversold: {symbols} \u2014 {date_str}"

        return f"True Value Oversold: {count} Candidates \u2014 {date_str}"

    def send_email(self, subject: str, html_content: str) -> bool:
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
            logger.error(f"Failed to send email: {e}")
            return False
