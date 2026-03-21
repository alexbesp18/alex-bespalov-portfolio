#!/usr/bin/env python3
"""
Analyze scrape data to identify underperforming parameter combinations.

Requires: 2+ weeks of daily scrape data for statistical significance.

Usage:
    python scripts/analyze_permutations.py --report
    python scripts/analyze_permutations.py --dimension nights
    python scripts/analyze_permutations.py --export results.csv
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

os.environ.setdefault('DB_MODE', 'supabase')

import pandas as pd
import numpy as np

from supabase import create_client
from config.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)

# Day of week mapping (Postgres DOW: 0=Sun, 1=Mon, ..., 6=Sat)
DOW_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']


def get_analysis_data() -> pd.DataFrame:
    """Fetch deal data from the analysis view."""
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_key)

    result = client.table('us_deal_analysis').select('*').execute()

    if not result.data:
        logger.warning("No data found in us_deal_analysis view")
        return pd.DataFrame()

    df = pd.DataFrame(result.data)
    logger.info(f"Loaded {len(df)} deals for analysis")
    return df


def analyze_dimension(df: pd.DataFrame, dimension: str, metric: str = 'yield_ratio') -> pd.DataFrame:
    """
    Analyze performance across a single dimension.

    Returns DataFrame with mean, median, max, count, and std for each value.
    """
    if df.empty or dimension not in df.columns:
        return pd.DataFrame()

    grouped = df.groupby(dimension)[metric].agg([
        ('mean', 'mean'),
        ('median', 'median'),
        ('max', 'max'),
        ('min', 'min'),
        ('std', 'std'),
        ('count', 'count'),
    ]).round(2)

    # Add win rate (% of deals above median)
    overall_median = df[metric].median()
    win_rates = df.groupby(dimension)[metric].apply(
        lambda x: (x > overall_median).mean() * 100
    ).round(1)
    grouped['win_rate'] = win_rates

    return grouped.sort_values('mean', ascending=False)


def calculate_effect_size(group_a: pd.Series, group_b: pd.Series) -> float:
    """Calculate Cohen's d effect size between two groups."""
    if len(group_a) < 2 or len(group_b) < 2:
        return 0.0

    n1, n2 = len(group_a), len(group_b)
    var1, var2 = group_a.var(), group_b.var()

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    if pooled_std == 0:
        return 0.0

    return abs(group_a.mean() - group_b.mean()) / pooled_std


def compare_values(df: pd.DataFrame, dimension: str, value_a, value_b, metric: str = 'yield_ratio') -> Dict:
    """
    Compare two values of a dimension.

    Returns win rate and effect size.
    """
    group_a = df[df[dimension] == value_a][metric]
    group_b = df[df[dimension] == value_b][metric]

    if len(group_a) < 10 or len(group_b) < 10:
        return {'insufficient_data': True}

    # Win rate: % of group_a deals that beat group_b median
    win_rate_a = (group_a > group_b.median()).mean() * 100
    effect_size = calculate_effect_size(group_a, group_b)

    return {
        f'{value_a}_mean': round(group_a.mean(), 2),
        f'{value_b}_mean': round(group_b.mean(), 2),
        f'{value_a}_win_rate': round(win_rate_a, 1),
        'effect_size': round(effect_size, 2),
    }


def classify_performance(win_rate: float, effect_size: float) -> str:
    """
    Classify parameter performance based on win rate and effect size.

    Returns: ELIMINATE, REDUCE, KEEP, or PRIORITIZE
    """
    if win_rate < 30 and effect_size > 0.5:
        return 'ELIMINATE'
    elif win_rate < 45 and effect_size > 0.3:
        return 'REDUCE'
    elif win_rate > 55:
        return 'PRIORITIZE'
    else:
        return 'KEEP'


def generate_report(df: pd.DataFrame) -> str:
    """Generate comprehensive permutation analysis report."""
    lines = []
    lines.append("=" * 60)
    lines.append("PERMUTATION ANALYSIS REPORT")
    lines.append("=" * 60)

    if df.empty:
        lines.append("\nInsufficient data. Need 2+ weeks of daily scrapes.")
        lines.append("Current deal count: 0")
        return '\n'.join(lines)

    # Data summary
    date_range = ""
    if 'scraped_at' in df.columns:
        min_date = pd.to_datetime(df['scraped_at']).min()
        max_date = pd.to_datetime(df['scraped_at']).max()
        days = (max_date - min_date).days
        date_range = f" ({days} days)"

    lines.append(f"\nData: {len(df):,} deals{date_range}")
    if 'city_name' in df.columns:
        lines.append(f"Cities: {df['city_name'].nunique()}")
    lines.append(f"Avg yield: {df['yield_ratio'].mean():.1f} LP/$")
    lines.append(f"Max yield: {df['yield_ratio'].max():.1f} LP/$")

    # Analyze each dimension
    dimensions = {
        'nights': 'Duration (nights)',
        'check_in_dow': 'Check-in Day',
        'adults': 'Adults',
        'stars': 'Star Rating',
    }

    eliminate = []
    reduce = []
    prioritize = []

    for dim, label in dimensions.items():
        if dim not in df.columns:
            continue

        lines.append(f"\n--- {label} ---")
        analysis = analyze_dimension(df, dim)

        if analysis.empty:
            lines.append("  Insufficient data")
            continue

        for value, row in analysis.iterrows():
            # Format value for display
            if dim == 'check_in_dow':
                display_val = DOW_NAMES[int(value)] if 0 <= value <= 6 else value
            else:
                display_val = value

            status = classify_performance(row['win_rate'], row.get('std', 0) / row['mean'] if row['mean'] > 0 else 0)

            lines.append(f"  {display_val}: mean={row['mean']:.1f}, win_rate={row['win_rate']:.0f}%, n={int(row['count'])}")

            if status == 'ELIMINATE':
                eliminate.append(f"{label}={display_val}: {row['win_rate']:.0f}% win rate")
            elif status == 'REDUCE':
                reduce.append(f"{label}={display_val}: {row['win_rate']:.0f}% win rate")
            elif status == 'PRIORITIZE':
                prioritize.append(f"{label}={display_val}: {row['win_rate']:.0f}% win rate")

    # Advance window buckets
    if 'advance_days' in df.columns:
        lines.append("\n--- Advance Booking Window ---")
        df['advance_bucket'] = pd.cut(
            df['advance_days'],
            bins=[0, 7, 14, 30, 100],
            labels=['1-7d', '8-14d', '15-30d', '30+d']
        )
        analysis = analyze_dimension(df, 'advance_bucket')
        for bucket, row in analysis.iterrows():
            lines.append(f"  {bucket}: mean={row['mean']:.1f}, win_rate={row['win_rate']:.0f}%, n={int(row['count'])}")

    # Recommendations
    lines.append("\n" + "=" * 60)
    lines.append("RECOMMENDATIONS")
    lines.append("=" * 60)

    if eliminate:
        lines.append("\nELIMINATE (consistently underperform):")
        for item in eliminate:
            lines.append(f"  - {item}")

    if reduce:
        lines.append("\nREDUCE (marginal underperformers):")
        for item in reduce:
            lines.append(f"  - {item}")

    if prioritize:
        lines.append("\nPRIORITIZE (consistent winners):")
        for item in prioritize:
            lines.append(f"  - {item}")

    if not eliminate and not reduce and not prioritize:
        lines.append("\nNo clear winners or losers yet. Need more data for reliable recommendations.")

    # Estimated impact
    if eliminate:
        current_perms = 80  # Estimate
        reduction = len(eliminate) * 10
        lines.append(f"\nESTIMATED SAVINGS:")
        lines.append(f"  Current permutations: ~{current_perms} per city")
        lines.append(f"  After elimination: ~{current_perms - reduction} per city")
        lines.append(f"  API calls reduced: {reduction / current_perms * 100:.0f}%")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Analyze scrape permutation performance')
    parser.add_argument('--report', action='store_true', help='Generate full report')
    parser.add_argument('--dimension', type=str, help='Analyze specific dimension')
    parser.add_argument('--export', type=str, help='Export raw data to CSV')
    args = parser.parse_args()

    logger.info("Loading analysis data...")
    df = get_analysis_data()

    if args.export:
        df.to_csv(args.export, index=False)
        logger.info(f"Exported {len(df)} rows to {args.export}")
        return

    if args.dimension:
        analysis = analyze_dimension(df, args.dimension)
        print(f"\nAnalysis by {args.dimension}:")
        print(analysis.to_string())
        return

    # Default: generate report
    report = generate_report(df)
    print(report)


if __name__ == '__main__':
    main()
