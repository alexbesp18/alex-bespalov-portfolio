"""
Backtest report generation.

Generates human-readable and structured reports from backtest results.
"""

from typing import List, Optional

from .models import (
    BacktestResult, SignalEvent, HorizonMetrics,
    ConvictionLevel
)


def generate_backtest_report(result: BacktestResult, detailed: bool = False) -> str:
    """
    Generate a human-readable backtest report.

    Args:
        result: BacktestResult from backtest run
        detailed: Include individual signal details

    Returns:
        Formatted report string
    """
    lines = []

    # Header
    lines.append("=" * 70)
    lines.append("BACKTEST REPORT")
    lines.append("=" * 70)
    lines.append("")

    # Metadata
    lines.append("CONFIGURATION")
    lines.append("-" * 40)
    lines.append(f"Signal Type:     {result.signal_type.value}")
    lines.append(f"Tickers:         {len(result.tickers)} symbols")
    lines.append(f"Date Range:      {result.start_date} to {result.end_date}")
    if result.conviction_filter:
        lines.append(f"Conviction Filter: {result.conviction_filter.value}+")
    lines.append(f"Total Signals:   {result.total_signals}")
    lines.append("")

    # Overall metrics by horizon
    lines.append("OVERALL PERFORMANCE")
    lines.append("-" * 40)
    lines.append(_format_metrics_table([
        result.metrics_2w,
        result.metrics_2m,
        result.metrics_6m,
    ]))
    lines.append("")

    # Breakdown by conviction
    if result.metrics_by_conviction:
        lines.append("PERFORMANCE BY CONVICTION LEVEL")
        lines.append("-" * 40)

        for conv in [ConvictionLevel.HIGH, ConvictionLevel.MEDIUM, ConvictionLevel.LOW]:
            if conv in result.metrics_by_conviction:
                lines.append(f"\n{conv.value} Conviction:")
                conv_metrics = result.metrics_by_conviction[conv]
                lines.append(_format_metrics_table([
                    conv_metrics.get('2w'),
                    conv_metrics.get('2m'),
                    conv_metrics.get('6m'),
                ]))

    lines.append("")

    # Signal summary by ticker
    lines.append("SIGNALS BY TICKER")
    lines.append("-" * 40)
    ticker_counts = {}
    for s in result.signals:
        ticker_counts[s.ticker] = ticker_counts.get(s.ticker, 0) + 1

    for ticker, count in sorted(ticker_counts.items(), key=lambda x: -x[1])[:20]:
        high = len([s for s in result.signals if s.ticker == ticker and s.conviction == ConvictionLevel.HIGH])
        med = len([s for s in result.signals if s.ticker == ticker and s.conviction == ConvictionLevel.MEDIUM])
        lines.append(f"  {ticker:8} {count:3} signals (HIGH: {high}, MED: {med})")

    if len(ticker_counts) > 20:
        lines.append(f"  ... and {len(ticker_counts) - 20} more tickers")

    lines.append("")

    # Best and worst signals
    if result.signals:
        lines.append("TOP 10 BEST SIGNALS (6-month return)")
        lines.append("-" * 40)
        sorted_by_return = sorted(
            [s for s in result.signals if s.return_6m is not None],
            key=lambda x: x.return_6m or 0,
            reverse=True
        )[:10]

        for s in sorted_by_return:
            conv_icon = "🔥" if s.conviction == ConvictionLevel.HIGH else "⚡" if s.conviction == ConvictionLevel.MEDIUM else "💤"
            lines.append(
                f"  {conv_icon} {s.ticker:6} {s.signal_date} | "
                f"Score: {s.score:4.1f} | "
                f"2w: {s.return_2w:+6.1f}% | "
                f"2m: {s.return_2m:+6.1f}% | "
                f"6m: {s.return_6m:+6.1f}%"
            )

        lines.append("")
        lines.append("TOP 10 WORST SIGNALS (6-month return)")
        lines.append("-" * 40)
        sorted_by_return = sorted(
            [s for s in result.signals if s.return_6m is not None],
            key=lambda x: x.return_6m or 0
        )[:10]

        for s in sorted_by_return:
            conv_icon = "🔥" if s.conviction == ConvictionLevel.HIGH else "⚡" if s.conviction == ConvictionLevel.MEDIUM else "💤"
            lines.append(
                f"  {conv_icon} {s.ticker:6} {s.signal_date} | "
                f"Score: {s.score:4.1f} | "
                f"2w: {s.return_2w:+6.1f}% | "
                f"2m: {s.return_2m:+6.1f}% | "
                f"6m: {s.return_6m:+6.1f}%"
            )

    lines.append("")

    # Key insights
    lines.append("KEY INSIGHTS")
    lines.append("-" * 40)
    lines.extend(_generate_insights(result))

    lines.append("")
    lines.append("=" * 70)

    # Detailed signal list
    if detailed and result.signals:
        lines.append("")
        lines.append("DETAILED SIGNAL LIST")
        lines.append("=" * 70)
        for s in sorted(result.signals, key=lambda x: x.signal_date):
            lines.append(_format_signal_detail(s))
            lines.append("")

    return "\n".join(lines)


def _format_metrics_table(metrics_list: List[Optional[HorizonMetrics]]) -> str:
    """Format metrics as a table row."""
    lines = []
    lines.append(f"{'Horizon':<10} {'Signals':<10} {'Win Rate':<12} {'Avg Return':<12} {'Expectancy':<12}")
    lines.append("-" * 56)

    for m in metrics_list:
        if m is None:
            continue
        horizon_label = {
            '2w': '2 Weeks',
            '2m': '2 Months',
            '6m': '6 Months',
        }.get(m.horizon, m.horizon)

        lines.append(
            f"{horizon_label:<10} "
            f"{m.signals_with_data:<10} "
            f"{m.win_rate:>5.1f}%      "
            f"{m.avg_return:>+6.2f}%     "
            f"{m.expectancy:>+6.2f}%"
        )

    return "\n".join(lines)


def _format_signal_detail(s: SignalEvent) -> str:
    """Format a single signal with full details."""
    conv_icon = "🔥" if s.conviction == ConvictionLevel.HIGH else "⚡" if s.conviction == ConvictionLevel.MEDIUM else "💤"

    return (
        f"{conv_icon} {s.ticker} — {s.signal_date}\n"
        f"   Score: {s.score}/10 | Conviction: {s.conviction.value}\n"
        f"   Volume: {s.volume_ratio}x | ADX: {s.adx_value}\n"
        f"   Price: ${s.price_at_signal:.2f}\n"
        f"   Returns: 2w={s.return_2w:+.1f}% | 2m={s.return_2m:+.1f}% | 6m={s.return_6m:+.1f}%\n"
        f"   Max Gain/Loss: 2w={s.max_gain_2w:+.1f}%/{s.max_loss_2w:+.1f}% | "
        f"2m={s.max_gain_2m:+.1f}%/{s.max_loss_2m:+.1f}%"
    )


def _generate_insights(result: BacktestResult) -> List[str]:
    """Generate actionable insights from backtest results."""
    insights = []

    # Compare HIGH vs MEDIUM conviction
    if ConvictionLevel.HIGH in result.metrics_by_conviction and ConvictionLevel.MEDIUM in result.metrics_by_conviction:
        high_2m = result.metrics_by_conviction[ConvictionLevel.HIGH].get('2m')
        med_2m = result.metrics_by_conviction[ConvictionLevel.MEDIUM].get('2m')

        if high_2m and med_2m and high_2m.signals_with_data > 0 and med_2m.signals_with_data > 0:
            if high_2m.win_rate > med_2m.win_rate:
                diff = high_2m.win_rate - med_2m.win_rate
                insights.append(f"✅ HIGH conviction has {diff:.1f}% better win rate than MEDIUM at 2-month horizon")
            else:
                diff = med_2m.win_rate - high_2m.win_rate
                insights.append(f"⚠️ MEDIUM conviction outperforms HIGH by {diff:.1f}% — review thresholds")

    # Overall win rate assessment
    if result.metrics_2m and result.metrics_2m.signals_with_data > 0:
        if result.metrics_2m.win_rate >= 60:
            insights.append(f"✅ Strong 2-month win rate: {result.metrics_2m.win_rate:.1f}%")
        elif result.metrics_2m.win_rate >= 50:
            insights.append(f"⚡ Acceptable 2-month win rate: {result.metrics_2m.win_rate:.1f}%")
        else:
            insights.append(f"⚠️ Weak 2-month win rate: {result.metrics_2m.win_rate:.1f}% — signals too loose")

    # Expectancy check
    if result.metrics_2m and result.metrics_2m.expectancy > 0:
        insights.append(f"✅ Positive expectancy at 2-month: {result.metrics_2m.expectancy:.2f}%")
    elif result.metrics_2m:
        insights.append(f"⚠️ Negative expectancy at 2-month: {result.metrics_2m.expectancy:.2f}% — edge not working")

    # Signal frequency
    if result.total_signals > 0:
        days = (result.end_date - result.start_date).days or 1
        signals_per_month = result.total_signals / (days / 30)
        insights.append(f"📊 Signal frequency: ~{signals_per_month:.1f} signals/month")

    # HIGH conviction scarcity
    high_signals = len(result.high_conviction_signals)
    if high_signals == 0:
        insights.append("⚠️ No HIGH conviction signals detected — thresholds may be too strict")
    else:
        pct_high = high_signals / result.total_signals * 100
        insights.append(f"📊 HIGH conviction: {high_signals} signals ({pct_high:.1f}% of total)")

    return insights


def generate_csv_report(result: BacktestResult) -> str:
    """Generate CSV-formatted signal data for export."""
    lines = []

    # Header
    lines.append(",".join([
        "ticker", "date", "signal_type", "conviction", "score",
        "volume_ratio", "adx", "price",
        "return_2w", "return_2m", "return_6m",
        "max_gain_2w", "max_loss_2w",
        "max_gain_2m", "max_loss_2m",
        "max_gain_6m", "max_loss_6m",
    ]))

    for s in result.signals:
        lines.append(",".join([
            s.ticker,
            str(s.signal_date),
            s.signal_type.value,
            s.conviction.value,
            str(s.score),
            str(s.volume_ratio),
            str(s.adx_value),
            str(s.price_at_signal),
            str(s.return_2w or ""),
            str(s.return_2m or ""),
            str(s.return_6m or ""),
            str(s.max_gain_2w or ""),
            str(s.max_loss_2w or ""),
            str(s.max_gain_2m or ""),
            str(s.max_loss_2m or ""),
            str(s.max_gain_6m or ""),
            str(s.max_loss_6m or ""),
        ]))

    return "\n".join(lines)
