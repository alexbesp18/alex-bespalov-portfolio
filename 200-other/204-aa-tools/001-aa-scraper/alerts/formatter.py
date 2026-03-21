"""
Email formatter for AA Points Monitor.
Generates HTML and text content for alerts and digests.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from config.settings import get_settings
from core.scorer import is_expiring_soon
from core.optimizer import TopPick, AllocationResult
from core.database import get_database


# =============================================================================
# HTML Building Helpers (extracted for reusability and reduced complexity)
# =============================================================================

def build_html_table(
    headers: List[Tuple[str, str]],  # (label, alignment: left/center/right)
    rows: List[List[str]],
    header_bg: str = "#e3f2fd",
) -> str:
    """
    Build an HTML table with consistent styling.

    Args:
        headers: List of (header_text, alignment) tuples
        rows: List of row data (list of cell strings)
        header_bg: Header background color

    Returns:
        HTML table string
    """
    # Build header row
    header_cells = ""
    for label, align in headers:
        header_cells += f'<th style="padding: 10px; text-align: {align};">{label}</th>'

    # Build data rows
    row_html = ""
    for row_data in rows:
        cells = ""
        for i, cell in enumerate(row_data):
            align = headers[i][1] if i < len(headers) else "left"
            cells += f'<td style="padding: 8px; text-align: {align};">{cell}</td>'
        row_html += f"<tr>{cells}</tr>"

    return f"""
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: {header_bg};">
            {header_cells}
        </tr>
        {row_html}
    </table>
    """


def build_section_card(
    title: str,
    subtitle: str,
    content_html: str,
    title_color: str = "#1e3a5f",
    icon: str = "",
) -> str:
    """
    Build a digest section card with consistent styling.

    Args:
        title: Section title
        subtitle: Subtitle/description
        content_html: Inner HTML content (usually a table)
        title_color: Title text color
        icon: Optional emoji icon

    Returns:
        HTML card string
    """
    title_text = f"{icon} {title}" if icon else title
    return f"""
    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="margin-top: 0; color: {title_color};">{title_text}</h2>
        <p style="color: #666; margin-top: 0;">{subtitle}</p>
        {content_html}
    </div>
    """


def format_stacked_section(deals: List[Dict[str, Any]], settings) -> Tuple[str, str]:
    """Format the stacked deals section for digest."""
    if not deals:
        return "", ""

    headers = [
        ("Merchant", "left"),
        ("Yield", "center"),
        ("Min Spend", "center"),
        ("Earnings", "right"),
    ]

    rows = []
    text_lines = []

    for i, deal in enumerate(deals[:10], 1):
        merchant = deal.get('merchant_name', 'Unknown')
        score = deal.get('deal_score', 0)
        min_spend = deal.get('min_spend_required', deal.get('min_spend', 0))
        total_miles = deal.get('total_miles', 0)
        icon = "🔥" if score >= settings.thresholds.stack_immediate_alert else "✅"

        rows.append([
            f"{icon} {merchant}",
            f"{score:.1f} LP/$",
            f"${min_spend:.0f}",
            f"{total_miles:,} LPs",
        ])
        text_lines.append(f"{i}. {icon} {merchant} — {score:.1f} LP/$ (spend ${min_spend:.0f}, earn {total_miles:,} LPs)")

    table_html = build_html_table(headers, rows, header_bg="#e3f2fd")
    section_html = build_section_card(
        title="Stacked Deals (Portal + SimplyMiles)",
        subtitle="Best combo: click through portal, pay with AA card after activating SimplyMiles",
        content_html=table_html,
        title_color="#1e3a5f",
        icon="🔗",
    )

    section_text = "🔗 STACKED DEALS (Portal + SimplyMiles)\n" + "\n".join(text_lines)
    return section_html, section_text


def format_simplymiles_section(deals: List[Dict[str, Any]]) -> Tuple[str, str]:
    """Format the SimplyMiles-only section for digest."""
    if not deals:
        return "", ""

    headers = [
        ("Merchant", "left"),
        ("Yield", "center"),
        ("Spend", "center"),
        ("Earnings", "right"),
    ]

    rows = []
    text_lines = []

    for deal in deals[:5]:
        merchant = deal.get('merchant_name', 'Unknown')
        yield_ratio = deal.get('yield_ratio', deal.get('deal_score', 0))
        miles = deal.get('miles_amount', 0)
        lp = deal.get('lp_amount', 0)
        total = deal.get('total_miles', miles + lp)
        min_spend = deal.get('min_spend', 0)
        offer_type = deal.get('offer_type', 'flat_bonus')

        spend_info = f"${min_spend:.0f}" if offer_type == 'flat_bonus' and min_spend else "per $"

        rows.append([
            f"💳 {merchant}",
            f"{yield_ratio:.1f} LP/$",
            spend_info,
            f"{total:,} LPs",
        ])
        text_lines.append(f"💳 {merchant} — {yield_ratio:.1f} LP/$ ({spend_info} → {total:,} LPs)")

    table_html = build_html_table(headers, rows, header_bg="#f3e5f5")
    section_html = build_section_card(
        title="SimplyMiles Only",
        subtitle="Card-linked offers (no portal needed)",
        content_html=table_html,
        title_color="#7b1fa2",
        icon="💳",
    )

    section_text = "\n\n💳 SIMPLYMILES ONLY (Card-linked)\n" + "\n".join(text_lines)
    return section_html, section_text


def format_portal_section(deals: List[Dict[str, Any]]) -> Tuple[str, str]:
    """Format the Portal-only section for digest."""
    if not deals:
        return "", ""

    headers = [
        ("Merchant", "left"),
        ("Portal Rate", "center"),
        ("Total Yield", "right"),
    ]

    rows = []
    text_lines = []

    for deal in deals[:5]:
        merchant = deal.get('merchant_name', 'Unknown')
        portal_rate = deal.get('portal_rate', 0)
        total_yield = deal.get('total_yield', deal.get('deal_score', 0))
        is_bonus = deal.get('is_bonus', False)
        bonus_tag = " 🔥" if is_bonus else ""

        rows.append([
            f"🛒 {merchant}{bonus_tag}",
            f"{portal_rate:.0f} mi/$",
            f"{total_yield:.0f} LP/$ total",
        ])
        text_lines.append(f"🛒 {merchant} — {portal_rate:.0f} mi/$ portal + 1 mi/$ CC = {total_yield:.0f} LP/$ total{bonus_tag}")

    table_html = build_html_table(headers, rows, header_bg="#e0f2f1")
    section_html = build_section_card(
        title="AA Shopping Portal Only",
        subtitle="High portal rates (no SimplyMiles offer available)",
        content_html=table_html,
        title_color="#00796b",
        icon="🛒",
    )

    section_text = "\n\n🛒 AA SHOPPING PORTAL ONLY\n" + "\n".join(text_lines)
    return section_html, section_text


def format_top_pick_section(top_pick: Optional[TopPick]) -> Tuple[str, str]:
    """Format the top pick section for digest."""
    if not top_pick:
        return "", ""

    expires_note = ""
    if top_pick.expires_at:
        try:
            exp_dt = datetime.fromisoformat(top_pick.expires_at.replace('Z', '+00:00'))
            expires_note = f" (expires {exp_dt.strftime('%m/%d')})"
        except ValueError:
            pass

    section_html = f"""
    <div style="background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="margin: 0 0 10px 0;">🎯 TOP PICK TODAY</h2>
        <p style="font-size: 28px; margin: 0; font-weight: bold;">{top_pick.merchant_name}</p>
        <p style="font-size: 24px; margin: 10px 0;">{top_pick.deal_score:.0f} LP/$ — spend ${top_pick.min_spend:.0f}, earn {top_pick.total_miles:,} LPs{expires_note}</p>
        <p style="margin: 10px 0 0 0; font-style: italic;">WHY: {top_pick.why_text}</p>
    </div>
    """

    section_text = f"""
🎯 TOP PICK TODAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{top_pick.merchant_name} — {top_pick.deal_score:.0f} LP/$
Spend ${top_pick.min_spend:.0f} → Earn {top_pick.total_miles:,} LPs{expires_note}
WHY: {top_pick.why_text}
"""
    return section_html, section_text


def format_allocation_section(allocation: Optional[AllocationResult]) -> Tuple[str, str]:
    """Format the budget allocation section for digest."""
    if not allocation or not allocation.allocations:
        return "", ""

    headers = [
        ("Deal", "left"),
        ("Spend", "center"),
        ("Earnings", "right"),
    ]

    rows = []
    text_lines = []

    for alloc in allocation.allocations[:8]:
        qty_str = f"{alloc.quantity}×" if alloc.quantity > 1 else ""
        rows.append([
            f"{qty_str} {alloc.merchant_name}",
            f"${alloc.total_spend:.0f}",
            f"{alloc.total_miles:,} LPs",
        ])
        text_lines.append(f"  {qty_str} {alloc.merchant_name} (${alloc.total_spend:.0f}) → {alloc.total_miles:,} LPs")

    table_html = build_html_table(headers, rows, header_bg="#ffecb3")

    # Add totals row
    remaining_note = f' | Remaining: ${allocation.remaining_budget:.0f}' if allocation.remaining_budget > 10 else ''
    totals_html = f"""
    <tr style="border-top: 2px solid #f57c00; font-weight: bold;">
        <td style="padding: 12px;">TOTAL</td>
        <td style="padding: 12px; text-align: center;">${allocation.total_spent:.0f}</td>
        <td style="padding: 12px; text-align: right;">{allocation.total_miles:,} LPs</td>
    </tr>
    </table>
    <p style="margin: 15px 0 0 0; text-align: center;">
        <strong>Blended yield: {allocation.blended_yield:.1f} LP/$</strong>{remaining_note}
    </p>
    """
    # Replace closing table tag with totals
    table_html = table_html.replace("</table>", totals_html)

    section_html = f"""
    <div style="background: #fff8e1; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
        <h2 style="margin-top: 0; color: #f57c00;">💰 Optimal ${allocation.budget:.0f} Allocation</h2>
        {table_html}
    </div>
    """

    section_text = f"""
💰 OPTIMAL ${allocation.budget:.0f} ALLOCATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join(text_lines)}

Total: ${allocation.total_spent:.0f} → {allocation.total_miles:,} LPs
Blended yield: {allocation.blended_yield:.1f} LP/$
"""
    return section_html, section_text


def check_hotel_vs_expectation(deal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare a hotel deal to its expected yield from the matrix.

    Args:
        deal: Hotel deal dictionary with city, check_in, yield_ratio

    Returns:
        Dict with:
          - expected_yield: Average from matrix for this combo
          - actual_yield: Deal's actual yield
          - beats_expected: True if > 20% above expected
          - vs_expected_pct: Percentage vs expected
    """
    db = get_database()
    city = deal.get('city', '')
    check_in = deal.get('check_in', '')
    check_out = deal.get('check_out', '')
    actual_yield = deal.get('yield_ratio', deal.get('deal_score', 0))

    if not city or not check_in:
        return {'beats_expected': False, 'vs_expected_pct': 0}

    try:
        # Parse check_in to get day_of_week and advance_days
        if isinstance(check_in, str):
            check_in_dt = datetime.fromisoformat(check_in.replace('Z', '+00:00'))
        else:
            check_in_dt = check_in

        day_of_week = check_in_dt.weekday()
        advance_days = (check_in_dt.date() - datetime.now().date()).days

        # Calculate duration
        if check_out:
            if isinstance(check_out, str):
                check_out_dt = datetime.fromisoformat(check_out.replace('Z', '+00:00'))
            else:
                check_out_dt = check_out
            duration = (check_out_dt.date() - check_in_dt.date()).days
        else:
            duration = 1

        # Get prediction from matrix
        prediction = db.get_matrix_yield_prediction(city, day_of_week, duration, advance_days)

        if prediction and prediction.get('avg_yield'):
            expected = prediction['avg_yield']
            vs_expected = ((actual_yield / expected) - 1) * 100 if expected > 0 else 0
            beats = vs_expected > 20  # 20% above expected

            return {
                'expected_yield': expected,
                'actual_yield': actual_yield,
                'beats_expected': beats,
                'vs_expected_pct': vs_expected
            }
    except (ValueError, TypeError):
        pass

    return {'beats_expected': False, 'vs_expected_pct': 0}


def format_immediate_alert(deal: Dict[str, Any], deal_type: str = 'stack') -> Dict[str, str]:
    """
    Format an immediate alert email for a single deal.

    Args:
        deal: Deal dictionary
        deal_type: 'stack' or 'hotel'

    Returns:
        Dict with 'subject', 'html', and 'text' keys
    """
    if deal_type == 'hotel':
        return _format_hotel_alert(deal)
    return _format_stack_alert(deal)


def _format_hotel_alert(deal: Dict[str, Any]) -> Dict[str, str]:
    """Format an immediate alert for a hotel deal."""
    settings = get_settings()

    hotel_name = deal.get('hotel_name', 'Unknown Hotel')
    city = deal.get('city', '')
    state = deal.get('state', '')
    score = deal.get('deal_score', deal.get('yield_ratio', 0))
    nightly_rate = deal.get('nightly_rate', 0)
    nights = deal.get('nights', 1)
    total_cost = deal.get('total_cost', nightly_rate * nights)
    base_miles = deal.get('base_miles', 0)
    bonus_miles = deal.get('bonus_miles', 0)
    total_miles = deal.get('total_miles', base_miles + bonus_miles)
    check_in = deal.get('check_in', '')

    subject = f"🏨 AA Hotel Alert: {score:.0f} LP/$ in {city}!"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0d47a1 100%); color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">🏨 {score:.0f} LP/$</h1>
            <p style="margin: 10px 0 0 0; font-size: 18px;">{hotel_name}</p>
            <p style="margin: 5px 0 0 0;">{city}, {state}</p>
        </div>

        <div style="padding: 20px; background: #f5f5f5;">
            <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="margin-top: 0; color: #1e3a5f;">Deal Summary</h2>

                <p style="font-size: 24px; margin: 0;">
                    💵 <strong>${total_cost:.0f}</strong> ({nights} night{'s' if nights > 1 else ''}) → <strong>{total_miles:,} LPs</strong>
                </p>
                {f'<p style="margin-top: 10px;">📅 Check-in: {check_in}</p>' if check_in else ''}
            </div>

            <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="margin-top: 0; color: #1e3a5f;">Breakdown</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0;">🏨 Base Miles</td>
                        <td style="padding: 8px 0; text-align: right;"><strong>{base_miles:,} miles</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0;">✨ Bonus Miles</td>
                        <td style="padding: 8px 0; text-align: right;"><strong>{bonus_miles:,} miles</strong></td>
                    </tr>
                    <tr style="border-top: 2px solid #1e3a5f; font-weight: bold;">
                        <td style="padding: 12px 0;">📈 TOTAL YIELD</td>
                        <td style="padding: 12px 0; text-align: right; color: #2e7d32;">{score:.1f} LP/$</td>
                    </tr>
                </table>
            </div>

            <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #1e3a5f;">
                <h3 style="margin-top: 0; color: #1e3a5f;">🎯 Action Required</h3>
                <p style="margin: 0;">Book through <a href="https://www.aadvantagehotels.com">AA Advantage Hotels</a></p>
            </div>
        </div>

        <div style="padding: 20px; text-align: center; color: #666; font-size: 12px;">
            <p>Status Progress: Gold → Platinum | Gap: {settings.lp_gap:,} LPs</p>
        </div>
    </div>
    """

    text = f"""
🏨 AA HOTEL ALERT: {score:.0f} LP/$ in {city}!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{hotel_name}
{city}, {state}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💵 Cost: ${total_cost:.0f} ({nights} night{'s' if nights > 1 else ''})
✈️ Total Earnings: {total_miles:,} LPs

Breakdown:
  • Base Miles: {base_miles:,}
  • Bonus Miles: {bonus_miles:,}

📈 YIELD: {score:.1f} LP/$

Book at: https://www.aadvantagehotels.com
"""

    return {
        'subject': subject,
        'html': html,
        'text': text
    }


def _format_stack_alert(deal: Dict[str, Any]) -> Dict[str, str]:
    """Format an immediate alert for a stacked shopping deal."""
    settings = get_settings()

    merchant = deal.get('merchant_name', 'Unknown')
    score = deal.get('deal_score', 0)
    min_spend = deal.get('min_spend_required', deal.get('min_spend', 0))
    total_miles = deal.get('total_miles', 0)

    # Build breakdown
    portal_miles = deal.get('portal_miles', 0)
    portal_rate = deal.get('portal_rate', 0)
    simplymiles_miles = deal.get('simplymiles_miles', 0)
    simplymiles_type = deal.get('simplymiles_type', 'flat_bonus')
    cc_miles = deal.get('cc_miles', 0)

    expires = deal.get('simplymiles_expires', '')
    expiring_soon = is_expiring_soon(expires) if expires else False

    subject = f"🔥 AA Points Alert: {score:.0f} LP/$ deal found!"

    # Expiration display
    expires_html = ""
    expires_text = ""
    if expires:
        try:
            exp_dt = datetime.fromisoformat(expires.replace('Z', '+00:00'))
            exp_str = exp_dt.strftime('%m/%d/%Y')
            if expiring_soon:
                expires_html = f'<p style="color: #d32f2f; font-weight: bold;">⏰ EXPIRES: {exp_str}</p>'
                expires_text = f"⏰ EXPIRES: {exp_str} (SOON!)"
            else:
                expires_html = f'<p>⏰ Expires: {exp_str}</p>'
                expires_text = f"⏰ Expires: {exp_str}"
        except ValueError:
            pass

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0d47a1 100%); color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">🔥 {score:.0f} LP/$</h1>
            <p style="margin: 10px 0 0 0; font-size: 18px;">{merchant}</p>
        </div>

        <div style="padding: 20px; background: #f5f5f5;">
            <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="margin-top: 0; color: #1e3a5f;">Deal Summary</h2>

                <p style="font-size: 24px; margin: 0;">
                    💵 <strong>Spend ${min_spend:.0f}</strong> → Earn <strong>{total_miles:,} LPs</strong>
                </p>

                {expires_html}
            </div>

            <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="margin-top: 0; color: #1e3a5f;">Breakdown</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0;">🛒 eShopping Portal</td>
                        <td style="padding: 8px 0; text-align: right;">{portal_rate:.0f} mi/$ × ${min_spend:.0f} = <strong>{portal_miles:,} miles</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0;">✨ SimplyMiles</td>
                        <td style="padding: 8px 0; text-align: right;">{'Bonus' if simplymiles_type == 'flat_bonus' else 'Per $'} = <strong>{simplymiles_miles:,} miles</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0;">💳 AA Mastercard</td>
                        <td style="padding: 8px 0; text-align: right;">1 mi/$ × ${min_spend:.0f} = <strong>{cc_miles:,} miles</strong></td>
                    </tr>
                    <tr style="border-top: 2px solid #1e3a5f; font-weight: bold;">
                        <td style="padding: 12px 0;">📈 TOTAL YIELD</td>
                        <td style="padding: 12px 0; text-align: right; color: #2e7d32;">{score:.1f} LP/$</td>
                    </tr>
                </table>
            </div>

            <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #1e3a5f;">
                <h3 style="margin-top: 0; color: #1e3a5f;">🎯 Action Required</h3>
                <ol style="margin: 0; padding-left: 20px;">
                    <li style="margin-bottom: 8px;"><strong>Click through the eShopping portal first</strong></li>
                    <li style="margin-bottom: 8px;">Activate offer on SimplyMiles</li>
                    <li style="margin-bottom: 8px;">Pay with your AA Mastercard</li>
                </ol>
            </div>
        </div>

        <div style="padding: 20px; text-align: center; color: #666; font-size: 12px;">
            <p>Status Progress: Gold → Platinum | Gap: {settings.lp_gap:,} LPs</p>
            <p><a href="https://www.aadvantageeshopping.com">eShopping Portal</a> | <a href="https://www.simplymiles.com">SimplyMiles</a></p>
        </div>
    </div>
    """

    text = f"""
🔥 AA POINTS ALERT: {score:.0f} LP/$ deal found!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 STACKED OPPORTUNITY: {merchant}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💵 Minimum Spend: ${min_spend:.0f}
✈️ Total Earnings: {total_miles:,} LPs

Breakdown:
  • Portal: {portal_rate:.0f} mi/$ × ${min_spend:.0f} = {portal_miles:,} miles
  • SimplyMiles: {simplymiles_miles:,} {'bonus' if simplymiles_type == 'flat_bonus' else 'per $'} miles
  • Credit Card: {cc_miles:,} miles

📈 YIELD: {score:.1f} LP/$
{expires_text}

ACTION REQUIRED:
1. Click through eShopping portal first
2. Activate offer on SimplyMiles
3. Pay with your AA Mastercard

Portal: https://www.aadvantageeshopping.com
SimplyMiles: https://www.simplymiles.com
"""

    return {
        'subject': subject,
        'html': html,
        'text': text
    }


def format_batch_alert(
    stack_deals: List[Dict[str, Any]],
    hotel_deals: List[Dict[str, Any]],
    simplymiles_only: Optional[List[Dict[str, Any]]] = None,
    portal_only: Optional[List[Dict[str, Any]]] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Format a rich immediate alert email with ALL deal categories.

    Args:
        stack_deals: List of stacked deals above immediate threshold
        hotel_deals: List of hotel deals above immediate threshold
        simplymiles_only: SimplyMiles deals without portal match
        portal_only: Portal deals without SimplyMiles match
        context: Optional context enrichment (historical comparison, patterns)

    Returns:
        Dict with 'subject', 'html', and 'text' keys
    """
    settings = get_settings()
    simplymiles_only = simplymiles_only or []
    portal_only = portal_only or []
    context = context or {}

    total_deals = len(stack_deals) + len(hotel_deals) + len(simplymiles_only) + len(portal_only)

    # Find the best deal for subject line
    best_score = 0
    best_merchant = ""
    if stack_deals:
        best_stack = max(stack_deals, key=lambda x: x.get('deal_score', 0))
        if best_stack.get('deal_score', 0) > best_score:
            best_score = best_stack.get('deal_score', 0)
            best_merchant = best_stack.get('merchant_name', '')
    if hotel_deals:
        best_hotel = max(hotel_deals, key=lambda x: x.get('deal_score', x.get('yield_ratio', 0)))
        score = best_hotel.get('deal_score', best_hotel.get('yield_ratio', 0))
        if score > best_score:
            best_score = score
            best_merchant = best_hotel.get('hotel_name', '')

    subject = f"🔥 {total_deals} High-Value Deals Found! Top: {best_score:.0f} LP/$"

    # Build hero section for the triggering deal
    hero_html = ""
    hero_text = ""
    if best_merchant:
        ctx_note = ""
        if context.get('vs_average_pct'):
            pct = context['vs_average_pct']
            ctx_note = f'<span style="background: #4caf50; color: white; padding: 4px 10px; border-radius: 12px; font-size: 14px; margin-left: 10px;">{pct:+.0f}% above average</span>'

        hero_html = f"""
        <div style="background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); color: white; padding: 25px; text-align: center;">
            <p style="margin: 0; font-size: 16px; opacity: 0.9;">🎯 TOP DEAL</p>
            <h1 style="margin: 10px 0; font-size: 42px;">{best_score:.0f} LP/$</h1>
            <p style="margin: 0; font-size: 22px;">{best_merchant}{ctx_note}</p>
        </div>
        """
        hero_text = f"🎯 TOP DEAL: {best_merchant} — {best_score:.0f} LP/$"

    # Build stacked deals section
    stack_html, stack_text = format_stacked_section(stack_deals, settings)

    # Build SimplyMiles-only section
    sm_html, sm_text = format_simplymiles_section(simplymiles_only)

    # Build Portal-only section
    portal_html, portal_text = format_portal_section(portal_only)

    # Build hotel deals section with context
    hotel_html = ""
    hotel_text = ""
    if hotel_deals:
        hotel_rows = ""
        hotel_lines = []
        above_expected = 0

        for i, deal in enumerate(sorted(hotel_deals, key=lambda x: x.get('deal_score', x.get('yield_ratio', 0)), reverse=True)[:5], 1):
            hotel = deal.get('hotel_name', 'Unknown')
            city = deal.get('city', '')
            state = deal.get('state', '')
            score = deal.get('deal_score', deal.get('yield_ratio', 0))
            total_cost = deal.get('total_cost', 0)
            total_miles = deal.get('total_miles', 0)

            # Check against yield matrix expectation
            expectation = check_hotel_vs_expectation(deal)
            badge_html = ""
            badge_text = ""
            if expectation.get('beats_expected'):
                above_expected += 1
                vs_pct = expectation.get('vs_expected_pct', 0)
                badge_html = f'<span style="background: #4caf50; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px;">+{vs_pct:.0f}%</span>'
                badge_text = f" 🔥+{vs_pct:.0f}%"

            hotel_rows += f"""
            <tr>
                <td style="padding: 8px;">🏨 {hotel[:25]}{badge_html}</td>
                <td style="padding: 8px;">{city}</td>
                <td style="padding: 8px; text-align: center;">{score:.0f} LP/$</td>
                <td style="padding: 8px; text-align: right;">${total_cost:.0f} → {total_miles:,}</td>
            </tr>
            """
            hotel_lines.append(f"{i}. 🏨 {hotel}, {city} — {score:.0f} LP/$ (${total_cost:.0f} → {total_miles:,}){badge_text}")

        header_note = f' ({above_expected} beat expected)' if above_expected else ''
        hotel_html = build_section_card(
            title=f"Hotel Deals{header_note}",
            subtitle="Book through AAdvantage Hotels",
            content_html=f"""
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #e3f2fd;">
                    <th style="padding: 10px; text-align: left;">Hotel</th>
                    <th style="padding: 10px;">City</th>
                    <th style="padding: 10px; text-align: center;">Yield</th>
                    <th style="padding: 10px; text-align: right;">Value</th>
                </tr>
                {hotel_rows}
            </table>
            """,
            title_color="#1e3a5f",
            icon="🏨"
        )
        hotel_text = f"\n\n🏨 HOTEL DEALS{header_note}\n" + "\n".join(hotel_lines)

    # Quick actions section
    actions_html = f"""
    <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #1e3a5f;">
        <h3 style="margin-top: 0; color: #1e3a5f;">🎯 Quick Actions</h3>
        <p style="margin: 8px 0;"><a href="https://www.aadvantageeshopping.com" style="color: #1976d2;">eShopping Portal</a> — Click through first for shopping deals</p>
        <p style="margin: 8px 0;"><a href="https://www.simplymiles.com" style="color: #1976d2;">SimplyMiles</a> — Activate card-linked offers</p>
        <p style="margin: 8px 0;"><a href="https://www.aadvantagehotels.com" style="color: #1976d2;">AA Hotels</a> — Book hotel deals</p>
    </div>
    """

    actions_text = """
🎯 QUICK ACTIONS
- eShopping Portal: https://www.aadvantageeshopping.com
- SimplyMiles: https://www.simplymiles.com
- AA Hotels: https://www.aadvantagehotels.com
"""

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
        {hero_html}

        <div style="padding: 20px; background: #f5f5f5;">
            {actions_html}
            {stack_html}
            {sm_html}
            {portal_html}
            {hotel_html}
        </div>

        <div style="padding: 20px; text-align: center; color: #666; font-size: 12px;">
            <p>Status Progress: Gold → Platinum | Gap: {settings.lp_gap:,} LPs</p>
        </div>
    </div>
    """

    text = f"""
{hero_text}

{actions_text}
{stack_text}
{sm_text}
{portal_text}
{hotel_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status Progress: Gold → Platinum | Gap: {settings.lp_gap:,} LPs
"""

    return {
        'subject': subject,
        'html': html,
        'text': text
    }


def format_new_this_week_section(discoveries: List[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Format the 'New This Week' section for daily digest.

    Args:
        discoveries: List of discovery dicts with deal_type, deal_identifier, first_seen_at, best_yield_seen

    Returns:
        Tuple of (html, text)
    """
    if not discoveries:
        return "", ""

    # Group by deal type
    by_type = {'hotel': [], 'stack': [], 'simplymiles': [], 'portal': []}
    for d in discoveries:
        deal_type = d.get('deal_type', 'other')
        if deal_type in by_type:
            by_type[deal_type].append(d)

    rows_html = ""
    text_lines = []

    type_icons = {
        'hotel': '🏨',
        'stack': '🔗',
        'simplymiles': '💳',
        'portal': '🛒'
    }

    for deal_type, items in by_type.items():
        if not items:
            continue
        icon = type_icons.get(deal_type, '📌')
        for item in items[:3]:  # Max 3 per type
            identifier = item.get('deal_identifier', 'Unknown')
            yield_val = item.get('best_yield_seen', 0)
            first_seen = item.get('first_seen_at', '')

            # Parse first_seen for display
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
                seen_str = dt.strftime('%m/%d')
            except (ValueError, AttributeError):
                seen_str = "recently"

            rows_html += f"""
            <tr>
                <td style="padding: 8px;">{icon} {identifier}</td>
                <td style="padding: 8px; text-align: center;">{yield_val:.1f} LP/$</td>
                <td style="padding: 8px; text-align: right;">Found {seen_str}</td>
            </tr>
            """
            text_lines.append(f"{icon} {identifier} — {yield_val:.1f} LP/$ (found {seen_str})")

    if not rows_html:
        return "", ""

    html = f"""
    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #9c27b0;">
        <h2 style="margin-top: 0; color: #7b1fa2;">🆕 New This Week</h2>
        <p style="color: #666; margin-top: 0;">Deals discovered in the last 7 days</p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #f3e5f5;">
                <th style="padding: 10px; text-align: left;">Deal</th>
                <th style="padding: 10px; text-align: center;">Best Yield</th>
                <th style="padding: 10px; text-align: right;">First Seen</th>
            </tr>
            {rows_html}
        </table>
    </div>
    """

    text = "🆕 NEW THIS WEEK\n" + "\n".join(text_lines)
    return html, text


def format_daily_digest(
    stacked_deals: List[Dict[str, Any]],
    hotel_deals: List[Dict[str, Any]],
    expiring_deals: List[Dict[str, Any]],
    health_status: Optional[Dict[str, Any]] = None,
    top_pick: Optional[TopPick] = None,
    allocation: Optional[AllocationResult] = None,
    simplymiles_only: Optional[List[Dict[str, Any]]] = None,
    portal_only: Optional[List[Dict[str, Any]]] = None,
    new_this_week: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Format the daily digest email with 3 deal categories.

    Args:
        stacked_deals: Top stacked opportunities (Portal + SimplyMiles overlap)
        hotel_deals: Top hotel deals
        expiring_deals: Deals expiring soon
        health_status: Scraper health status (optional)
        top_pick: The single best deal with explanation (optional)
        allocation: Optimal budget allocation (optional)
        simplymiles_only: SimplyMiles deals without portal match (optional)
        portal_only: Portal deals without SimplyMiles match (optional)
        new_this_week: List of deals discovered in last 7 days (optional)

    Returns:
        Dict with 'subject', 'html', and 'text' keys
    """
    settings = get_settings()
    today = datetime.now().strftime('%B %d, %Y')

    simplymiles_only = simplymiles_only or []
    portal_only = portal_only or []
    new_this_week = new_this_week or []
    total_deals = len(stacked_deals) + len(hotel_deals) + len(simplymiles_only) + len(portal_only)

    # Format "New This Week" section
    new_this_week_html, new_this_week_text = format_new_this_week_section(new_this_week)

    # Use top pick in subject if available
    if top_pick:
        subject = f"🎯 AA Points: {top_pick.deal_score:.0f} LP/$ top pick + {total_deals} deals"
    else:
        subject = f"✈️ AA Points Daily Digest - {total_deals} opportunities found"

    # Format stacked deals section
    stacked_html = ""
    stacked_text = ""

    if stacked_deals:
        stacked_rows = ""
        stacked_lines = []

        for i, deal in enumerate(stacked_deals[:10], 1):
            merchant = deal.get('merchant_name', 'Unknown')
            score = deal.get('deal_score', 0)
            min_spend = deal.get('min_spend_required', deal.get('min_spend', 0))
            total_miles = deal.get('total_miles', 0)

            icon = "🔥" if score >= settings.thresholds.stack_immediate_alert else "✅"

            stacked_rows += f"""
            <tr>
                <td style="padding: 8px;">{icon} {merchant}</td>
                <td style="padding: 8px; text-align: center;">{score:.1f} LP/$</td>
                <td style="padding: 8px; text-align: center;">${min_spend:.0f}</td>
                <td style="padding: 8px; text-align: right;">{total_miles:,} LPs</td>
            </tr>
            """
            stacked_lines.append(f"{i}. {icon} {merchant} — {score:.1f} LP/$ (spend ${min_spend:.0f}, earn {total_miles:,} LPs)")

        stacked_html = f"""
        <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="margin-top: 0; color: #1e3a5f;">🔗 Stacked Deals (Portal + SimplyMiles)</h2>
            <p style="color: #666; margin-top: 0;">Best combo: click through portal, pay with AA card after activating SimplyMiles</p>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #e3f2fd;">
                    <th style="padding: 10px; text-align: left;">Merchant</th>
                    <th style="padding: 10px; text-align: center;">Yield</th>
                    <th style="padding: 10px; text-align: center;">Min Spend</th>
                    <th style="padding: 10px; text-align: right;">Earnings</th>
                </tr>
                {stacked_rows}
            </table>
        </div>
        """
        stacked_text = "🔗 STACKED DEALS (Portal + SimplyMiles)\n" + "\n".join(stacked_lines)

    # Format SimplyMiles-only section
    sm_only_html = ""
    sm_only_text = ""

    if simplymiles_only:
        sm_rows = ""
        sm_lines = []

        for deal in simplymiles_only[:5]:
            merchant = deal.get('merchant_name', 'Unknown')
            yield_ratio = deal.get('yield_ratio', deal.get('deal_score', 0))
            miles = deal.get('miles_amount', 0)
            lp = deal.get('lp_amount', 0)
            total = deal.get('total_miles', miles + lp)
            min_spend = deal.get('min_spend', 0)
            offer_type = deal.get('offer_type', 'flat_bonus')

            if offer_type == 'flat_bonus' and min_spend:
                spend_info = f"${min_spend:.0f}"
            else:
                spend_info = "per $"

            sm_rows += f"""
            <tr>
                <td style="padding: 8px;">💳 {merchant}</td>
                <td style="padding: 8px; text-align: center;">{yield_ratio:.1f} LP/$</td>
                <td style="padding: 8px; text-align: center;">{spend_info}</td>
                <td style="padding: 8px; text-align: right;">{total:,} LPs</td>
            </tr>
            """
            sm_lines.append(f"💳 {merchant} — {yield_ratio:.1f} LP/$ ({spend_info} → {total:,} LPs)")

        sm_only_html = f"""
        <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="margin-top: 0; color: #7b1fa2;">💳 SimplyMiles Only</h2>
            <p style="color: #666; margin-top: 0;">Card-linked offers (no portal needed)</p>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #f3e5f5;">
                    <th style="padding: 10px; text-align: left;">Merchant</th>
                    <th style="padding: 10px; text-align: center;">Yield</th>
                    <th style="padding: 10px; text-align: center;">Spend</th>
                    <th style="padding: 10px; text-align: right;">Earnings</th>
                </tr>
                {sm_rows}
            </table>
        </div>
        """
        sm_only_text = "\n\n💳 SIMPLYMILES ONLY (Card-linked)\n" + "\n".join(sm_lines)

    # Format Portal-only section
    portal_only_html = ""
    portal_only_text = ""

    if portal_only:
        portal_rows = ""
        portal_lines = []

        for deal in portal_only[:5]:
            merchant = deal.get('merchant_name', 'Unknown')
            portal_rate = deal.get('portal_rate', 0)
            total_yield = deal.get('total_yield', deal.get('deal_score', 0))
            is_bonus = deal.get('is_bonus', False)

            bonus_tag = " 🔥" if is_bonus else ""

            portal_rows += f"""
            <tr>
                <td style="padding: 8px;">🛒 {merchant}{bonus_tag}</td>
                <td style="padding: 8px; text-align: center;">{portal_rate:.0f} mi/$</td>
                <td style="padding: 8px; text-align: right;">{total_yield:.0f} LP/$ total</td>
            </tr>
            """
            portal_lines.append(f"🛒 {merchant} — {portal_rate:.0f} mi/$ portal + 1 mi/$ CC = {total_yield:.0f} LP/$ total{bonus_tag}")

        portal_only_html = f"""
        <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="margin-top: 0; color: #00796b;">🛒 AA Shopping Portal Only</h2>
            <p style="color: #666; margin-top: 0;">High portal rates (no SimplyMiles offer available)</p>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #e0f2f1;">
                    <th style="padding: 10px; text-align: left;">Merchant</th>
                    <th style="padding: 10px; text-align: center;">Portal Rate</th>
                    <th style="padding: 10px; text-align: right;">Total Yield</th>
                </tr>
                {portal_rows}
            </table>
        </div>
        """
        portal_only_text = "\n\n🛒 AA SHOPPING PORTAL ONLY\n" + "\n".join(portal_lines)

    # Format Top Pick section
    top_pick_html = ""
    top_pick_text = ""

    if top_pick:
        expires_note = ""
        if top_pick.expires_at:
            try:
                exp_dt = datetime.fromisoformat(top_pick.expires_at.replace('Z', '+00:00'))
                expires_note = f" (expires {exp_dt.strftime('%m/%d')})"
            except ValueError:
                pass

        top_pick_html = f"""
        <div style="background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="margin: 0 0 10px 0;">🎯 TOP PICK TODAY</h2>
            <p style="font-size: 28px; margin: 0; font-weight: bold;">{top_pick.merchant_name}</p>
            <p style="font-size: 24px; margin: 10px 0;">{top_pick.deal_score:.0f} LP/$ — spend ${top_pick.min_spend:.0f}, earn {top_pick.total_miles:,} LPs{expires_note}</p>
            <p style="margin: 10px 0 0 0; font-style: italic;">WHY: {top_pick.why_text}</p>
        </div>
        """

        top_pick_text = f"""
🎯 TOP PICK TODAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{top_pick.merchant_name} — {top_pick.deal_score:.0f} LP/$
Spend ${top_pick.min_spend:.0f} → Earn {top_pick.total_miles:,} LPs{expires_note}
WHY: {top_pick.why_text}
"""

    # Format Allocation section
    allocation_html = ""
    allocation_text = ""

    if allocation and allocation.allocations:
        alloc_rows = ""
        alloc_lines = []

        for alloc in allocation.allocations[:8]:  # Top 8 allocations
            qty_str = f"{alloc.quantity}×" if alloc.quantity > 1 else ""
            alloc_rows += f"""
            <tr>
                <td style="padding: 8px;">{qty_str} {alloc.merchant_name}</td>
                <td style="padding: 8px; text-align: center;">${alloc.total_spend:.0f}</td>
                <td style="padding: 8px; text-align: right;">{alloc.total_miles:,} LPs</td>
            </tr>
            """
            alloc_lines.append(f"  {qty_str} {alloc.merchant_name} (${alloc.total_spend:.0f}) → {alloc.total_miles:,} LPs")

        allocation_html = f"""
        <div style="background: #fff8e1; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <h2 style="margin-top: 0; color: #f57c00;">💰 Optimal ${allocation.budget:.0f} Allocation</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #ffecb3;">
                    <th style="padding: 10px; text-align: left;">Deal</th>
                    <th style="padding: 10px; text-align: center;">Spend</th>
                    <th style="padding: 10px; text-align: right;">Earnings</th>
                </tr>
                {alloc_rows}
                <tr style="border-top: 2px solid #f57c00; font-weight: bold;">
                    <td style="padding: 12px;">TOTAL</td>
                    <td style="padding: 12px; text-align: center;">${allocation.total_spent:.0f}</td>
                    <td style="padding: 12px; text-align: right;">{allocation.total_miles:,} LPs</td>
                </tr>
            </table>
            <p style="margin: 15px 0 0 0; text-align: center;">
                <strong>Blended yield: {allocation.blended_yield:.1f} LP/$</strong>
                {f' | Remaining: ${allocation.remaining_budget:.0f}' if allocation.remaining_budget > 10 else ''}
            </p>
        </div>
        """

        allocation_text = f"""
💰 OPTIMAL ${allocation.budget:.0f} ALLOCATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join(alloc_lines)}

Total: ${allocation.total_spent:.0f} → {allocation.total_miles:,} LPs
Blended yield: {allocation.blended_yield:.1f} LP/$
"""

    # Format hotel deals section with deviation-based indicators
    hotel_html = ""
    hotel_text = ""

    if hotel_deals:
        hotel_rows = ""
        hotel_lines = []
        significant_count = 0

        for i, deal in enumerate(hotel_deals[:5], 1):
            hotel = deal.get('hotel_name', 'Unknown')
            city = deal.get('city', '')
            state = deal.get('state', '')
            score = deal.get('deal_score', deal.get('yield_ratio', 0))
            cost = deal.get('total_cost', 0)
            miles = deal.get('total_miles', 0)

            # Check for significance reason from filter_significant_hotels()
            significance_reason = deal.get('significance_reason')
            deviation_pct = deal.get('deviation_pct')

            badge_html = ""
            badge_text = ""

            if significance_reason:
                significant_count += 1
                if deviation_pct is not None:
                    badge_html = f'<span style="background: #4caf50; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px;">+{deviation_pct:.0f}% above typical</span>'
                    badge_text = f" 🔥 +{deviation_pct:.0f}% above typical"
                else:
                    badge_html = f'<span style="background: #ff9800; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px;">{significance_reason}</span>'
                    badge_text = f" 🔥 {significance_reason}"
            else:
                # Fallback: check against yield matrix expectation
                expectation = check_hotel_vs_expectation(deal)
                if expectation.get('beats_expected'):
                    significant_count += 1
                    vs_pct = expectation.get('vs_expected_pct', 0)
                    badge_html = f'<span style="background: #4caf50; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px;">+{vs_pct:.0f}% vs expected</span>'
                    badge_text = f" 🔥 +{vs_pct:.0f}% above expected"

            hotel_rows += f"""
            <tr>
                <td style="padding: 8px;">{hotel}{badge_html}</td>
                <td style="padding: 8px;">{city}, {state}</td>
                <td style="padding: 8px; text-align: center;">{score:.1f} LP/$</td>
                <td style="padding: 8px; text-align: right;">${cost:.0f} → {miles:,} LPs</td>
            </tr>
            """
            hotel_lines.append(f"{i}. {hotel}, {city} — {score:.1f} LP/$ (${cost:.0f} → {miles:,} LPs){badge_text}")

        # Add section header note if any deals are significant
        header_note = f' <span style="color: #4caf50;">({significant_count} above typical)</span>' if significant_count else ''

        hotel_html = f"""
        <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="margin-top: 0; color: #1e3a5f;">🏨 Top Hotel Deals{header_note}</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #e3f2fd;">
                    <th style="padding: 10px; text-align: left;">Hotel</th>
                    <th style="padding: 10px; text-align: left;">Location</th>
                    <th style="padding: 10px; text-align: center;">Yield</th>
                    <th style="padding: 10px; text-align: right;">Value</th>
                </tr>
                {hotel_rows}
            </table>
        </div>
        """
        header_text = f" ({significant_count} above typical)" if significant_count else ""
        hotel_text = f"\n\n🏨 TOP HOTEL DEALS{header_text}\n" + "\n".join(hotel_lines)

    # Format expiring section
    expiring_html = ""
    expiring_text = ""

    if expiring_deals:
        expiring_items = ""
        expiring_lines = []

        for deal in expiring_deals[:5]:
            merchant = deal.get('merchant_name', 'Unknown')
            score = deal.get('deal_score', 0)
            expires = deal.get('simplymiles_expires', '')

            try:
                exp_dt = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                exp_str = exp_dt.strftime('%m/%d')
            except (ValueError, AttributeError):
                exp_str = "Soon"

            expiring_items += f"<li>⏰ {merchant} — {score:.1f} LP/$ (expires {exp_str})</li>"
            expiring_lines.append(f"⏰ {merchant} — {score:.1f} LP/$ (expires {exp_str})")

        expiring_html = f"""
        <div style="background: #fff3e0; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #ff9800;">
            <h3 style="margin-top: 0; color: #e65100;">⏰ Expiring Soon</h3>
            <ul style="margin: 0; padding-left: 20px;">{expiring_items}</ul>
        </div>
        """
        expiring_text = "\n\n⏰ EXPIRING SOON\n" + "\n".join(expiring_lines)

    # Format health status
    health_html = ""
    health_text = ""

    if health_status:
        health_items = ""
        health_lines = []

        for scraper, status in health_status.items():
            if status.get('is_stale'):
                health_items += f"<li>⚠️ {scraper}: Data is stale (last: {status.get('age_hours', '?')}h ago)</li>"
                health_lines.append(f"⚠️ {scraper}: stale ({status.get('age_hours', '?')}h)")
            else:
                health_items += f"<li>✅ {scraper}: OK</li>"

        if health_items:
            health_html = f"""
            <div style="background: #fafafa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin-top: 0; color: #666;">System Health</h4>
                <ul style="margin: 0; padding-left: 20px; font-size: 14px;">{health_items}</ul>
            </div>
            """
            health_text = "\n\n📊 SYSTEM HEALTH\n" + "\n".join(health_lines)

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0d47a1 100%); color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">✈️ AA Points Arbitrage Report</h1>
            <p style="margin: 10px 0 0 0;">{today}</p>
        </div>

        <div style="padding: 20px; background: #f5f5f5;">
            {top_pick_html}
            {new_this_week_html}
            {allocation_html}
            {expiring_html}
            {stacked_html}
            {sm_only_html}
            {portal_only_html}
            {hotel_html}
            {health_html}

            <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; text-align: center;">
                <h3 style="margin-top: 0; color: #2e7d32;">Status Progress: Gold → Platinum</h3>
                <p style="font-size: 18px; margin: 0;">
                    Current: ~{settings.current_lp:,} LPs | Target: {settings.target_lp:,} LPs | <strong>Gap: {settings.lp_gap:,} LPs</strong>
                </p>
            </div>
        </div>

        <div style="padding: 20px; text-align: center; color: #666; font-size: 12px;">
            <p>Happy earning! 🎯</p>
        </div>
    </div>
    """

    text = f"""
✈️ AA POINTS ARBITRAGE REPORT - {today}
{top_pick_text}
{new_this_week_text}
{allocation_text}
{expiring_text}

{stacked_text}
{sm_only_text}
{portal_only_text}
{hotel_text}
{health_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status Progress: Gold → Platinum
Current: ~{settings.current_lp:,} LPs | Target: {settings.target_lp:,} LPs | Gap: {settings.lp_gap:,} LPs

Happy earning! 🎯
"""

    return {
        'subject': subject,
        'html': html,
        'text': text
    }

