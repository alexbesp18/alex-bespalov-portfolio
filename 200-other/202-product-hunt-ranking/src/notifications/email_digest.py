"""Weekly digest email for Product Hunt insights."""

import logging
import os
from datetime import date

import resend

from src.db.models import EnrichedProduct, PHWeeklyInsights

logger = logging.getLogger(__name__)


def _format_product_html(product: EnrichedProduct, rank: int) -> str:
    """Format a single product as HTML."""
    category_badge = ""
    if product.category:
        category_badge = f'<span style="background:#e0e0e0;padding:2px 6px;border-radius:3px;font-size:12px;margin-left:8px;">{product.category}</span>'

    scores = ""
    if product.innovation_score is not None or product.market_fit_score is not None:
        scores = '<div style="margin-top:8px;font-size:12px;color:#888;">'
        if product.innovation_score is not None:
            scores += f"Innovation: {product.innovation_score:.1f}/10 "
        if product.market_fit_score is not None:
            scores += f"| Market Fit: {product.market_fit_score:.1f}/10"
        scores += "</div>"

    # Use Grok's what_it_does if available, otherwise fall back to description
    description = product.description
    if product.maker_info and product.maker_info.get("what_it_does"):
        description = product.maker_info["what_it_does"]

    return f"""
    <tr style="border-bottom:1px solid #eee;">
        <td style="padding:16px 12px;text-align:center;font-weight:bold;color:#666;vertical-align:top;font-size:18px;">#{rank}</td>
        <td style="padding:16px 12px;">
            <div style="margin-bottom:8px;">
                <a href="{product.url}" style="color:#da552f;text-decoration:none;font-weight:bold;font-size:16px;">
                    {product.name}
                </a>
                {category_badge}
            </div>
            <p style="color:#444;font-size:14px;line-height:1.5;margin:0;">{description}</p>
            {scores}
        </td>
        <td style="padding:16px 12px;text-align:center;vertical-align:top;">
            <span style="color:#da552f;font-weight:bold;font-size:14px;">
                ▲ {product.upvotes}
            </span>
        </td>
    </tr>
    """


def _format_insights_html(insights: PHWeeklyInsights) -> str:
    """Format weekly insights as HTML."""
    trends_html = ""
    if insights.top_trends:
        trends_html = "<ul style='margin:0;padding-left:20px;'>"
        for trend in insights.top_trends[:5]:
            trends_html += f"<li style='margin:4px 0;'>{trend}</li>"
        trends_html += "</ul>"

    categories_html = ""
    if insights.category_breakdown:
        categories_html = "<div style='display:flex;flex-wrap:wrap;gap:8px;'>"
        for cat, count in sorted(
            insights.category_breakdown.items(), key=lambda x: x[1], reverse=True
        )[:6]:
            categories_html += f'<span style="background:#f0f0f0;padding:4px 8px;border-radius:4px;">{cat}: {count}</span>'
        categories_html += "</div>"

    sentiment_color = "#666"
    if insights.sentiment == "Bullish":
        sentiment_color = "#22c55e"
    elif insights.sentiment == "Bearish":
        sentiment_color = "#ef4444"

    return f"""
    <div style="background:#f9f9f9;padding:16px;border-radius:8px;margin-bottom:24px;">
        <h3 style="margin:0 0 12px 0;color:#333;">📊 Weekly Insights</h3>
        <p style="margin:8px 0;"><strong>Average Upvotes:</strong> {insights.avg_upvotes:.0f}</p>
        <p style="margin:8px 0;"><strong>Market Sentiment:</strong> <span style="color:{sentiment_color};font-weight:bold;">{insights.sentiment}</span></p>
        {f"<p style='margin:8px 0;'><strong>Top Trends:</strong></p>{trends_html}" if trends_html else ""}
        {f"<p style='margin:8px 0;'><strong>Categories:</strong></p>{categories_html}" if categories_html else ""}
        {f"<p style='margin:12px 0;color:#555;'>{insights.notable_launches}</p>" if insights.notable_launches else ""}
    </div>
    """


def build_digest_html(
    products: list[EnrichedProduct],
    insights: PHWeeklyInsights | None = None,
    week_date: date | None = None,
) -> str:
    """Build the complete digest email HTML."""
    week_str = week_date.strftime("%B %d, %Y") if week_date else "This Week"

    products_html = ""
    for i, product in enumerate(products[:10], 1):
        products_html += _format_product_html(product, i)

    insights_html = _format_insights_html(insights) if insights else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#fff;">
        <div style="text-align:center;margin-bottom:24px;">
            <h1 style="color:#da552f;margin:0;">🚀 Product Hunt Weekly</h1>
            <p style="color:#666;margin:8px 0;">Week of {week_str}</p>
        </div>

        {insights_html}

        <h2 style="color:#333;border-bottom:2px solid #da552f;padding-bottom:8px;">Top 10 Products</h2>

        <table style="width:100%;border-collapse:collapse;">
            <tbody>
                {products_html}
            </tbody>
        </table>

        <div style="text-align:center;margin-top:24px;padding:16px;background:#f9f9f9;border-radius:8px;">
            <p style="margin:0;color:#666;font-size:12px;">
                Generated by Product Hunt Weekly Tracker<br>
                <a href="https://www.producthunt.com/leaderboard/weekly" style="color:#da552f;">View on Product Hunt</a>
            </p>
        </div>
    </body>
    </html>
    """


def send_weekly_digest(
    products: list[EnrichedProduct],
    insights: PHWeeklyInsights | None = None,
    week_date: date | None = None,
    to_emails: list[str] | None = None,
    dry_run: bool = False,
) -> bool:
    """
    Send weekly digest email.

    Args:
        products: List of enriched products to include
        insights: Optional weekly insights
        week_date: Week date for the digest
        to_emails: Override recipient list
        dry_run: If True, log but don't send

    Returns:
        True if email sent successfully
    """
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("EMAIL_FROM", "digest@producthunt-tracker.com")
    recipients = to_emails or os.getenv("EMAIL_TO", "").split(",")
    recipients = [e.strip() for e in recipients if e.strip()]

    if not api_key:
        logger.warning("RESEND_API_KEY not set, skipping email")
        return False

    if not recipients:
        logger.warning("No email recipients configured, skipping email")
        return False

    week_str = week_date.strftime("%Y-%m-%d") if week_date else "This Week"
    subject = f"🚀 Product Hunt Weekly Digest - {week_str}"
    html = build_digest_html(products, insights, week_date)

    if dry_run:
        logger.info(f"[DRY RUN] Would send digest to: {recipients}")
        return True

    try:
        resend.api_key = api_key
        resend.Emails.send(
            {
                "from": from_email,
                "to": recipients,
                "subject": subject,
                "html": html,
            }
        )
        logger.info(f"Weekly digest sent to {len(recipients)} recipients")
        return True

    except Exception as e:
        logger.error(f"Failed to send digest email: {e}")
        return False
