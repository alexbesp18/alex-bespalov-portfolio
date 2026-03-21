"""
Hotel Yield Matrix Verification System

Tracks yield stability over time and schedules re-verification of stale/drifting entries.
Provides health metrics and prioritizes entries needing attention.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import logging

from core.database import get_database

logger = logging.getLogger(__name__)


@dataclass
class VerificationEntry:
    """An entry that needs verification."""
    city: str
    day_of_week: int
    duration: int
    advance_days: int
    last_verified_at: Optional[str]
    verification_count: int
    yield_stability: Optional[float]
    avg_yield: float
    priority_score: float
    reason: str


@dataclass
class MatrixHealth:
    """Overall health status of the yield matrix."""
    total_entries: int
    verified_this_week: int
    stale_count: int
    unstable_count: int
    under_verified_count: int
    avg_stability: float
    avg_verification_count: float
    oldest_verification_days: int
    needs_attention: List[VerificationEntry]


DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def get_entries_needing_verification(
    max_age_days: int = 7,
    min_stability: float = 0.85,
    min_verifications: int = 2,
    limit: int = 50
) -> List[VerificationEntry]:
    """
    Find matrix entries that need re-verification.

    Criteria (any match triggers inclusion):
    - last_verified_at > max_age_days old
    - yield_stability < min_stability (>15% drift)
    - verification_count < min_verifications

    Returns entries sorted by priority (highest first).
    """
    db = get_database()
    cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()

    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                city, day_of_week, duration, advance_days,
                last_verified_at, verification_count, yield_stability, avg_yield,
                CASE
                    WHEN last_verified_at IS NULL THEN 100
                    WHEN last_verified_at < ? THEN
                        50 + (julianday('now') - julianday(last_verified_at))
                    ELSE 0
                END as stale_score,
                CASE
                    WHEN yield_stability IS NULL THEN 30
                    WHEN yield_stability < ? THEN
                        40 * (1.0 - yield_stability)
                    ELSE 0
                END as instability_score,
                CASE
                    WHEN verification_count < ? THEN
                        20 * (? - verification_count)
                    ELSE 0
                END as underverified_score
            FROM hotel_yield_matrix
            WHERE
                last_verified_at IS NULL
                OR last_verified_at < ?
                OR yield_stability < ?
                OR verification_count < ?
            ORDER BY
                (stale_score + instability_score + underverified_score) DESC
            LIMIT ?
        """, (cutoff_date, min_stability, min_verifications, min_verifications,
              cutoff_date, min_stability, min_verifications, limit))

        entries = []
        for row in cursor.fetchall():
            # Determine primary reason
            reasons = []
            if row['last_verified_at'] is None or row['last_verified_at'] < cutoff_date:
                if row['last_verified_at']:
                    days_old = (datetime.now() - datetime.fromisoformat(row['last_verified_at'])).days
                    reasons.append(f"stale ({days_old}d old)")
                else:
                    reasons.append("never verified")
            if row['yield_stability'] and row['yield_stability'] < min_stability:
                drift_pct = (1 - row['yield_stability']) * 100
                reasons.append(f"unstable ({drift_pct:.0f}% drift)")
            if row['verification_count'] < min_verifications:
                reasons.append(f"under-verified ({row['verification_count']}x)")

            priority = (row['stale_score'] or 0) + (row['instability_score'] or 0) + (row['underverified_score'] or 0)

            entries.append(VerificationEntry(
                city=row['city'],
                day_of_week=row['day_of_week'],
                duration=row['duration'],
                advance_days=row['advance_days'],
                last_verified_at=row['last_verified_at'],
                verification_count=row['verification_count'],
                yield_stability=row['yield_stability'],
                avg_yield=row['avg_yield'],
                priority_score=priority,
                reason=", ".join(reasons)
            ))

        return entries


def get_stale_entries(days_old: int = 7, limit: int = 100) -> List[VerificationEntry]:
    """Get entries not verified in the last N days."""
    db = get_database()
    cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()

    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                city, day_of_week, duration, advance_days,
                last_verified_at, verification_count, yield_stability, avg_yield
            FROM hotel_yield_matrix
            WHERE last_verified_at IS NULL OR last_verified_at < ?
            ORDER BY last_verified_at ASC NULLS FIRST
            LIMIT ?
        """, (cutoff_date, limit))

        return [
            VerificationEntry(
                city=row['city'],
                day_of_week=row['day_of_week'],
                duration=row['duration'],
                advance_days=row['advance_days'],
                last_verified_at=row['last_verified_at'],
                verification_count=row['verification_count'],
                yield_stability=row['yield_stability'],
                avg_yield=row['avg_yield'],
                priority_score=0,
                reason="stale"
            )
            for row in cursor.fetchall()
        ]


def get_unstable_entries(max_stability: float = 0.85, limit: int = 50) -> List[VerificationEntry]:
    """Get entries with low yield stability (high drift)."""
    db = get_database()

    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                city, day_of_week, duration, advance_days,
                last_verified_at, verification_count, yield_stability, avg_yield
            FROM hotel_yield_matrix
            WHERE yield_stability IS NOT NULL AND yield_stability < ?
            ORDER BY yield_stability ASC
            LIMIT ?
        """, (max_stability, limit))

        return [
            VerificationEntry(
                city=row['city'],
                day_of_week=row['day_of_week'],
                duration=row['duration'],
                advance_days=row['advance_days'],
                last_verified_at=row['last_verified_at'],
                verification_count=row['verification_count'],
                yield_stability=row['yield_stability'],
                avg_yield=row['avg_yield'],
                priority_score=0,
                reason=f"unstable ({(1 - row['yield_stability']) * 100:.0f}% drift)"
            )
            for row in cursor.fetchall()
        ]


def get_matrix_health() -> MatrixHealth:
    """Get overall health metrics for the yield matrix."""
    db = get_database()
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()

    with db.get_connection() as conn:
        # Overall stats
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN last_verified_at >= ? THEN 1 ELSE 0 END) as verified_week,
                SUM(CASE WHEN last_verified_at < ? OR last_verified_at IS NULL THEN 1 ELSE 0 END) as stale,
                SUM(CASE WHEN yield_stability < 0.85 THEN 1 ELSE 0 END) as unstable,
                SUM(CASE WHEN verification_count < 2 THEN 1 ELSE 0 END) as under_verified,
                AVG(yield_stability) as avg_stability,
                AVG(verification_count) as avg_verifications,
                MIN(last_verified_at) as oldest_verification
            FROM hotel_yield_matrix
        """, (week_ago, week_ago))

        row = cursor.fetchone()

        # Calculate days since oldest verification
        oldest_days = 0
        if row['oldest_verification']:
            oldest_date = datetime.fromisoformat(row['oldest_verification'])
            oldest_days = (datetime.now() - oldest_date).days

        # Get top entries needing attention
        needs_attention = get_entries_needing_verification(limit=10)

        return MatrixHealth(
            total_entries=row['total'] or 0,
            verified_this_week=row['verified_week'] or 0,
            stale_count=row['stale'] or 0,
            unstable_count=row['unstable'] or 0,
            under_verified_count=row['under_verified'] or 0,
            avg_stability=row['avg_stability'] or 0,
            avg_verification_count=row['avg_verifications'] or 0,
            oldest_verification_days=oldest_days,
            needs_attention=needs_attention
        )


def format_health_report(health: MatrixHealth) -> str:
    """Format health metrics as a readable report."""
    lines = []
    lines.append("# Hotel Yield Matrix Health Report")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Summary stats
    lines.append("## Summary")
    lines.append(f"- **Total Entries:** {health.total_entries:,}")
    lines.append(f"- **Verified This Week:** {health.verified_this_week:,} ({health.verified_this_week / max(health.total_entries, 1) * 100:.1f}%)")
    lines.append(f"- **Average Stability:** {health.avg_stability:.2%}")
    lines.append(f"- **Average Verifications:** {health.avg_verification_count:.1f}x")
    lines.append(f"- **Oldest Verification:** {health.oldest_verification_days} days ago")
    lines.append("")

    # Issues
    lines.append("## Issues")
    lines.append(f"- **Stale (>7 days):** {health.stale_count:,}")
    lines.append(f"- **Unstable (<85%):** {health.unstable_count:,}")
    lines.append(f"- **Under-verified (<2x):** {health.under_verified_count:,}")
    lines.append("")

    # Health grade
    issues_pct = (health.stale_count + health.unstable_count) / max(health.total_entries, 1)
    if issues_pct < 0.1:
        grade = "A - Excellent"
    elif issues_pct < 0.25:
        grade = "B - Good"
    elif issues_pct < 0.5:
        grade = "C - Fair"
    else:
        grade = "D - Needs Attention"

    lines.append(f"## Overall Grade: {grade}")
    lines.append("")

    # Top entries needing attention
    if health.needs_attention:
        lines.append("## Top 10 Entries Needing Attention")
        lines.append("")
        lines.append("| City | Day | Dur | Adv | Yield | Stability | Reason |")
        lines.append("|------|-----|-----|-----|-------|-----------|--------|")
        for entry in health.needs_attention[:10]:
            day = DAY_NAMES[entry.day_of_week]
            stability = f"{entry.yield_stability:.0%}" if entry.yield_stability else "N/A"
            lines.append(f"| {entry.city} | {day} | {entry.duration}n | {entry.advance_days}d | {entry.avg_yield:.1f} | {stability} | {entry.reason} |")

    return "\n".join(lines)


def get_verification_combinations(limit: int = 50) -> List[Tuple[str, int, int, int]]:
    """
    Get list of (city, day_of_week, duration, advance_days) tuples
    that should be re-verified, in priority order.
    """
    entries = get_entries_needing_verification(limit=limit)
    return [
        (e.city, e.day_of_week, e.duration, e.advance_days)
        for e in entries
    ]


if __name__ == '__main__':
    # Quick health check when run directly
    health = get_matrix_health()
    print(format_health_report(health))
