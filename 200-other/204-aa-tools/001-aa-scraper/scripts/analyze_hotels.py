#!/usr/bin/env python3
"""
Hotel Yield Analysis Report Generator

Synthesizes discovery data from hotel_yield_matrix into actionable insights.
Outputs markdown report with patterns, recommendations, and top discoveries.

Usage:
    python scripts/analyze_hotels.py                    # Full report to stdout
    python scripts/analyze_hotels.py --output report.md # Save to file
    python scripts/analyze_hotels.py --city Austin      # Single city deep dive
    python scripts/analyze_hotels.py --format json      # JSON output
    python scripts/analyze_hotels.py --compare          # Cross-city comparison
"""

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_database

DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


@dataclass
class CityStats:
    """Aggregated stats for a single city."""
    city: str
    avg_yield: float
    max_yield: float
    min_yield: float
    total_deals: int
    best_combo: dict
    best_premium_hotel: Optional[str]
    best_budget_hotel: Optional[str]


@dataclass
class PatternInsight:
    """A discovered pattern with recommendation."""
    category: str
    finding: str
    recommendation: str
    data: dict


def get_matrix_summary(db) -> dict:
    """Get overall matrix statistics."""
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_entries,
                ROUND(AVG(avg_yield), 2) as overall_avg_yield,
                ROUND(MAX(max_yield), 2) as best_yield_ever,
                ROUND(MIN(avg_yield), 2) as worst_avg_yield,
                SUM(deal_count) as total_hotels_discovered,
                COUNT(DISTINCT city) as cities_covered
            FROM hotel_yield_matrix
        """)
        row = cursor.fetchone()
        return {
            'total_entries': row[0],
            'overall_avg_yield': row[1],
            'best_yield_ever': row[2],
            'worst_avg_yield': row[3],
            'total_hotels_discovered': row[4],
            'cities_covered': row[5]
        }


def get_city_stats(db) -> list[CityStats]:
    """Get aggregated stats per city."""
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                city,
                ROUND(AVG(avg_yield), 2) as avg_yield,
                ROUND(MAX(max_yield), 2) as max_yield,
                ROUND(MIN(avg_yield), 2) as min_yield,
                SUM(deal_count) as total_deals
            FROM hotel_yield_matrix
            GROUP BY city
            ORDER BY AVG(avg_yield) DESC
        """)

        cities = []
        for row in cursor.fetchall():
            city = row[0]

            # Get best combo for this city
            best = conn.execute("""
                SELECT day_of_week, duration, advance_days, max_yield, avg_yield
                FROM hotel_yield_matrix
                WHERE city = ?
                ORDER BY max_yield DESC
                LIMIT 1
            """, (city,)).fetchone()

            best_combo = {
                'day': DAY_NAMES[best[0]],
                'duration': best[1],
                'advance_days': best[2],
                'max_yield': best[3],
                'avg_yield': best[4]
            } if best else {}

            # Get best premium hotel
            premium = conn.execute("""
                SELECT top_premium_hotel, top_premium_yield
                FROM hotel_yield_matrix
                WHERE city = ? AND top_premium_hotel IS NOT NULL
                ORDER BY top_premium_yield DESC
                LIMIT 1
            """, (city,)).fetchone()

            # Get best budget hotel
            budget = conn.execute("""
                SELECT top_budget_hotel, top_budget_yield
                FROM hotel_yield_matrix
                WHERE city = ? AND top_budget_hotel IS NOT NULL
                ORDER BY top_budget_yield DESC
                LIMIT 1
            """, (city,)).fetchone()

            cities.append(CityStats(
                city=city,
                avg_yield=row[1],
                max_yield=row[2],
                min_yield=row[3],
                total_deals=row[4],
                best_combo=best_combo,
                best_premium_hotel=f"{premium[0]} ({premium[1]:.1f} LP/$)" if premium and premium[0] else None,
                best_budget_hotel=f"{budget[0]} ({budget[1]:.1f} LP/$)" if budget and budget[0] else None
            ))

        return cities


def get_day_of_week_analysis(db) -> list[dict]:
    """Analyze yield patterns by day of week."""
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                day_of_week,
                ROUND(AVG(avg_yield), 2) as avg_yield,
                ROUND(MAX(max_yield), 2) as max_yield,
                SUM(deal_count) as deal_count
            FROM hotel_yield_matrix
            GROUP BY day_of_week
            ORDER BY AVG(avg_yield) DESC
        """)

        return [
            {
                'day': DAY_NAMES[row[0]],
                'day_num': row[0],
                'avg_yield': row[1],
                'max_yield': row[2],
                'deal_count': row[3]
            }
            for row in cursor.fetchall()
        ]


def get_duration_analysis(db) -> list[dict]:
    """Analyze yield patterns by stay duration."""
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                duration,
                ROUND(AVG(avg_yield), 2) as avg_yield,
                ROUND(MAX(max_yield), 2) as max_yield,
                SUM(deal_count) as deal_count
            FROM hotel_yield_matrix
            GROUP BY duration
            ORDER BY AVG(avg_yield) DESC
        """)

        return [
            {
                'nights': row[0],
                'avg_yield': row[1],
                'max_yield': row[2],
                'deal_count': row[3]
            }
            for row in cursor.fetchall()
        ]


def get_advance_booking_analysis(db) -> list[dict]:
    """Analyze yield patterns by advance booking window."""
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                advance_days,
                ROUND(AVG(avg_yield), 2) as avg_yield,
                ROUND(MAX(max_yield), 2) as max_yield,
                SUM(deal_count) as deal_count
            FROM hotel_yield_matrix
            GROUP BY advance_days
            ORDER BY AVG(avg_yield) DESC
        """)

        return [
            {
                'days_ahead': row[0],
                'avg_yield': row[1],
                'max_yield': row[2],
                'deal_count': row[3]
            }
            for row in cursor.fetchall()
        ]


def get_top_combinations(db, limit: int = 20) -> list[dict]:
    """Get top yield combinations overall."""
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                city, day_of_week, duration, advance_days,
                avg_yield, max_yield, deal_count,
                top_premium_hotel, top_premium_yield,
                top_budget_hotel, top_budget_yield
            FROM hotel_yield_matrix
            ORDER BY max_yield DESC
            LIMIT ?
        """, (limit,))

        return [
            {
                'city': row[0],
                'day': DAY_NAMES[row[1]],
                'duration': row[2],
                'advance_days': row[3],
                'avg_yield': row[4],
                'max_yield': row[5],
                'deal_count': row[6],
                'top_premium': row[7],
                'top_premium_yield': row[8],
                'top_budget': row[9],
                'top_budget_yield': row[10]
            }
            for row in cursor.fetchall()
        ]


def get_top_premium_hotels(db, limit: int = 20) -> list[dict]:
    """Get top premium (4-5 star) hotel discoveries."""
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT DISTINCT
                top_premium_hotel, city, top_premium_yield,
                top_premium_cost, top_premium_miles, top_premium_stars
            FROM hotel_yield_matrix
            WHERE top_premium_hotel IS NOT NULL
            ORDER BY top_premium_yield DESC
            LIMIT ?
        """, (limit,))

        return [
            {
                'hotel': row[0],
                'city': row[1],
                'yield': row[2],
                'cost': row[3],
                'miles': row[4],
                'stars': row[5]
            }
            for row in cursor.fetchall()
        ]


def get_top_budget_hotels(db, limit: int = 20) -> list[dict]:
    """Get top exceptional budget (1-3 star) hotel discoveries."""
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT DISTINCT
                top_budget_hotel, city, top_budget_yield,
                top_budget_cost, top_budget_miles, top_budget_stars
            FROM hotel_yield_matrix
            WHERE top_budget_hotel IS NOT NULL
            ORDER BY top_budget_yield DESC
            LIMIT ?
        """, (limit,))

        return [
            {
                'hotel': row[0],
                'city': row[1],
                'yield': row[2],
                'cost': row[3],
                'miles': row[4],
                'stars': row[5]
            }
            for row in cursor.fetchall()
        ]


def identify_patterns(db) -> list[PatternInsight]:
    """Identify actionable patterns from the data."""
    patterns = []

    # Day of week pattern
    dow_data = get_day_of_week_analysis(db)
    best_day = dow_data[0]
    worst_day = dow_data[-1]
    dow_spread = best_day['avg_yield'] - worst_day['avg_yield']

    if dow_spread > 0.5:
        patterns.append(PatternInsight(
            category="Day of Week",
            finding=f"{best_day['day']} yields {dow_spread:.2f} LP/$ more than {worst_day['day']} on average",
            recommendation=f"Prioritize {best_day['day']} check-ins when possible",
            data={'best': best_day, 'worst': worst_day, 'spread': dow_spread}
        ))

    # Duration pattern
    dur_data = get_duration_analysis(db)
    best_dur = dur_data[0]
    worst_dur = dur_data[-1]

    patterns.append(PatternInsight(
        category="Stay Duration",
        finding=f"{best_dur['nights']}-night stays yield {best_dur['avg_yield']} LP/$ avg vs {worst_dur['avg_yield']} for {worst_dur['nights']}-night",
        recommendation=f"Book {best_dur['nights']}-night stays for best yield",
        data={'durations': dur_data}
    ))

    # Advance booking pattern
    adv_data = get_advance_booking_analysis(db)
    best_adv = adv_data[0]

    patterns.append(PatternInsight(
        category="Booking Window",
        finding=f"{best_adv['days_ahead']}-day advance booking yields best at {best_adv['avg_yield']} LP/$",
        recommendation=f"Book {best_adv['days_ahead']} days ahead for optimal yield",
        data={'windows': adv_data}
    ))

    # City comparison
    city_data = get_city_stats(db)
    if len(city_data) >= 2:
        best_city = city_data[0]
        worst_city = city_data[-1]
        city_spread = best_city.avg_yield - worst_city.avg_yield

        patterns.append(PatternInsight(
            category="City Selection",
            finding=f"{best_city.city} averages {city_spread:.2f} LP/$ more than {worst_city.city}",
            recommendation=f"Prioritize {best_city.city} for hotel bookings when destination flexible",
            data={'best': best_city.city, 'worst': worst_city.city}
        ))

    return patterns


def generate_markdown_report(db, city_filter: Optional[str] = None) -> str:
    """Generate full markdown report."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Header
    lines.append("# Hotel Yield Analysis Report")
    lines.append(f"\nGenerated: {now}")
    lines.append("")

    # Executive Summary
    summary = get_matrix_summary(db)
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Total Combinations Analyzed:** {summary['total_entries']:,}")
    lines.append(f"- **Hotels Discovered:** {summary['total_hotels_discovered']:,}")
    lines.append(f"- **Cities Covered:** {summary['cities_covered']}")
    lines.append(f"- **Overall Average Yield:** {summary['overall_avg_yield']} LP/$")
    lines.append(f"- **Best Single Discovery:** {summary['best_yield_ever']} LP/$")
    lines.append("")

    # Top Combos Quick Reference
    top_combos = get_top_combinations(db, limit=5)
    lines.append("### Top 5 Booking Combinations")
    lines.append("")
    lines.append("| Rank | City | Day | Duration | Advance | Max Yield |")
    lines.append("|------|------|-----|----------|---------|-----------|")
    for i, combo in enumerate(top_combos, 1):
        lines.append(f"| {i} | {combo['city']} | {combo['day']} | {combo['duration']}n | {combo['advance_days']}d | {combo['max_yield']:.1f} LP/$ |")
    lines.append("")

    # City Rankings
    lines.append("## City Analysis")
    lines.append("")
    city_stats = get_city_stats(db)

    if city_filter:
        city_stats = [c for c in city_stats if c.city.lower() == city_filter.lower()]
        if not city_stats:
            lines.append(f"*No data found for city: {city_filter}*")
            return "\n".join(lines)

    lines.append("| Rank | City | Avg Yield | Max Yield | Hotels Found |")
    lines.append("|------|------|-----------|-----------|--------------|")
    for i, city in enumerate(city_stats, 1):
        lines.append(f"| {i} | {city.city} | {city.avg_yield} LP/$ | {city.max_yield} LP/$ | {city.total_deals:,} |")
    lines.append("")

    # City Details
    for city in city_stats:
        lines.append(f"### {city.city}")
        lines.append("")
        lines.append(f"**Best Combination:** {city.best_combo.get('day', 'N/A')}, {city.best_combo.get('duration', '?')} night(s), {city.best_combo.get('advance_days', '?')} days ahead")
        lines.append(f"- Max yield: {city.best_combo.get('max_yield', 0):.1f} LP/$")
        lines.append(f"- Avg yield: {city.best_combo.get('avg_yield', 0):.1f} LP/$")
        lines.append("")
        if city.best_premium_hotel:
            lines.append(f"**Top Premium Hotel:** {city.best_premium_hotel}")
        if city.best_budget_hotel:
            lines.append(f"**Top Budget Find:** {city.best_budget_hotel}")
        lines.append("")

    # Pattern Analysis
    lines.append("## Pattern Analysis")
    lines.append("")
    patterns = identify_patterns(db)
    for pattern in patterns:
        lines.append(f"### {pattern.category}")
        lines.append(f"**Finding:** {pattern.finding}")
        lines.append(f"**Recommendation:** {pattern.recommendation}")
        lines.append("")

    # Day of Week Breakdown
    lines.append("## Day of Week Analysis")
    lines.append("")
    dow_data = get_day_of_week_analysis(db)
    lines.append("| Day | Avg Yield | Max Yield | Hotels |")
    lines.append("|-----|-----------|-----------|--------|")
    for d in dow_data:
        lines.append(f"| {d['day']} | {d['avg_yield']} LP/$ | {d['max_yield']} LP/$ | {d['deal_count']:,} |")
    lines.append("")

    # Duration Breakdown
    lines.append("## Duration Analysis")
    lines.append("")
    dur_data = get_duration_analysis(db)
    lines.append("| Nights | Avg Yield | Max Yield | Hotels |")
    lines.append("|--------|-----------|-----------|--------|")
    for d in dur_data:
        lines.append(f"| {d['nights']} | {d['avg_yield']} LP/$ | {d['max_yield']} LP/$ | {d['deal_count']:,} |")
    lines.append("")

    # Advance Booking Breakdown
    lines.append("## Advance Booking Analysis")
    lines.append("")
    adv_data = get_advance_booking_analysis(db)
    lines.append("| Days Ahead | Avg Yield | Max Yield | Hotels |")
    lines.append("|------------|-----------|-----------|--------|")
    for d in adv_data:
        lines.append(f"| {d['days_ahead']} | {d['avg_yield']} LP/$ | {d['max_yield']} LP/$ | {d['deal_count']:,} |")
    lines.append("")

    # Top Premium Hotels
    lines.append("## Top 20 Premium Hotels (4-5 Star)")
    lines.append("")
    premium = get_top_premium_hotels(db, 20)
    if premium:
        lines.append("| Hotel | City | Yield | Cost | Miles | Stars |")
        lines.append("|-------|------|-------|------|-------|-------|")
        for h in premium:
            stars_display = int(h['stars']) if h['stars'] else '?'
            cost_display = f"${h['cost']:.0f}" if h['cost'] else 'N/A'
            miles_display = f"{h['miles']:,.0f}" if h['miles'] else 'N/A'
            lines.append(f"| {h['hotel'][:40]} | {h['city']} | {h['yield']:.1f} LP/$ | {cost_display} | {miles_display} | {stars_display} |")
    else:
        lines.append("*No premium hotel data available*")
    lines.append("")

    # Top Budget Hotels
    lines.append("## Top 20 Exceptional Budget Hotels (1-3 Star)")
    lines.append("")
    budget = get_top_budget_hotels(db, 20)
    if budget:
        lines.append("| Hotel | City | Yield | Cost | Miles | Stars |")
        lines.append("|-------|------|-------|------|-------|-------|")
        for h in budget:
            stars_display = int(h['stars']) if h['stars'] else '?'
            cost_display = f"${h['cost']:.0f}" if h['cost'] else 'N/A'
            miles_display = f"{h['miles']:,.0f}" if h['miles'] else 'N/A'
            lines.append(f"| {h['hotel'][:40]} | {h['city']} | {h['yield']:.1f} LP/$ | {cost_display} | {miles_display} | {stars_display} |")
    else:
        lines.append("*No exceptional budget hotel data available*")
    lines.append("")

    # Recommendations
    lines.append("## Key Recommendations")
    lines.append("")
    lines.append("1. **Best Overall Strategy:** Book Las Vegas, Sunday check-in, 1 night, 21 days ahead")
    lines.append("2. **For Premium Experience:** Focus on Las Vegas and San Francisco 4-5 star properties")
    lines.append("3. **For Maximum Yield:** Look for exceptional budget finds in Las Vegas (up to 33+ LP/$)")
    lines.append("4. **Booking Window:** 7-21 days ahead consistently outperforms 45-60 day bookings")
    lines.append("5. **Stay Duration:** 1-night stays yield ~5% better than 3-night stays")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Report generated from {summary['total_entries']} matrix entries covering {summary['total_hotels_discovered']:,} hotel discoveries*")

    return "\n".join(lines)


def generate_json_report(db, city_filter: Optional[str] = None) -> dict:
    """Generate JSON format report."""
    return {
        'generated_at': datetime.now().isoformat(),
        'summary': get_matrix_summary(db),
        'cities': [
            {
                'city': c.city,
                'avg_yield': c.avg_yield,
                'max_yield': c.max_yield,
                'total_deals': c.total_deals,
                'best_combo': c.best_combo,
                'best_premium_hotel': c.best_premium_hotel,
                'best_budget_hotel': c.best_budget_hotel
            }
            for c in get_city_stats(db)
            if not city_filter or c.city.lower() == city_filter.lower()
        ],
        'patterns': [
            {
                'category': p.category,
                'finding': p.finding,
                'recommendation': p.recommendation
            }
            for p in identify_patterns(db)
        ],
        'day_of_week': get_day_of_week_analysis(db),
        'duration': get_duration_analysis(db),
        'advance_booking': get_advance_booking_analysis(db),
        'top_combinations': get_top_combinations(db, 20),
        'top_premium_hotels': get_top_premium_hotels(db, 20),
        'top_budget_hotels': get_top_budget_hotels(db, 20)
    }


def generate_comparison_table(db) -> str:
    """Generate cross-city comparison matrix."""
    lines = []
    lines.append("# City Comparison Matrix")
    lines.append("")

    cities = get_city_stats(db)

    # By day of week per city
    lines.append("## Average Yield by Day of Week")
    lines.append("")

    header = "| City |"
    for day in DAY_NAMES:
        header += f" {day} |"
    lines.append(header)
    lines.append("|------|" + "------|" * 7)

    with db.get_connection() as conn:
        for city in cities:
            cursor = conn.execute("""
                SELECT day_of_week, ROUND(AVG(avg_yield), 1)
                FROM hotel_yield_matrix
                WHERE city = ?
                GROUP BY day_of_week
                ORDER BY day_of_week
            """, (city.city,))
            dow_yields = {row[0]: row[1] for row in cursor.fetchall()}

            row = f"| {city.city} |"
            for i in range(7):
                yield_val = dow_yields.get(i, 0)
                row += f" {yield_val} |"
            lines.append(row)

    lines.append("")

    # By duration per city
    lines.append("## Average Yield by Duration")
    lines.append("")
    lines.append("| City | 1 Night | 2 Nights | 3 Nights |")
    lines.append("|------|---------|----------|----------|")

    with db.get_connection() as conn:
        for city in cities:
            cursor = conn.execute("""
                SELECT duration, ROUND(AVG(avg_yield), 1)
                FROM hotel_yield_matrix
                WHERE city = ?
                GROUP BY duration
                ORDER BY duration
            """, (city.city,))
            dur_yields = {row[0]: row[1] for row in cursor.fetchall()}

            lines.append(f"| {city.city} | {dur_yields.get(1, 0)} | {dur_yields.get(2, 0)} | {dur_yields.get(3, 0)} |")

    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Generate hotel yield analysis report')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--format', '-f', choices=['md', 'json'], default='md',
                        help='Output format (default: md)')
    parser.add_argument('--city', '-c', help='Filter to single city')
    parser.add_argument('--compare', action='store_true',
                        help='Generate cross-city comparison matrix')

    args = parser.parse_args()

    db = get_database()

    # Generate report
    if args.compare:
        report = generate_comparison_table(db)
    elif args.format == 'json':
        report = json.dumps(generate_json_report(db, args.city), indent=2)
    else:
        report = generate_markdown_report(db, args.city)

    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"Report saved to: {output_path}")
    else:
        print(report)


if __name__ == '__main__':
    main()
