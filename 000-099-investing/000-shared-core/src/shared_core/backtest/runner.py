#!/usr/bin/env python3
"""
Backtest Runner — CLI for running backtests on reversal signals.

Usage:
    python -m shared_core.backtest.runner --tickers AAPL,MSFT,GOOGL
    python -m shared_core.backtest.runner --all-sp500
    python -m shared_core.backtest.runner --tickers AAPL --detailed
"""

import argparse
import os
import sys
from datetime import date, timedelta
from typing import List, Dict, Optional

import pandas as pd

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .engine import BacktestEngine
from .models import SignalType, ConvictionLevel
from .report import generate_backtest_report, generate_csv_report


def load_ticker_data(
    tickers: List[str],
    api_key: Optional[str] = None,
    cache_dir: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, pd.DataFrame]:
    """
    Load historical data for tickers.

    Uses cached data if available, otherwise fetches from API.
    """
    from ..market_data.twelve_data import TwelveDataClient
    from ..cache.data_cache import DataCache

    # Initialize cache
    cache = None
    if cache_dir:
        cache = DataCache(cache_dir)

    # Get API key
    if not api_key:
        api_key = os.environ.get('TWELVE_DATA_API_KEY')

    if not api_key:
        print("Warning: No API key provided. Using cached data only.")

    # Initialize client
    client = TwelveDataClient(
        api_key=api_key or "",
        cache=cache,
        output_size=1000,  # 4 years
        verbose=verbose,
    )

    # Fetch data for each ticker
    ticker_data = {}

    for ticker in tickers:
        if verbose:
            print(f"Loading {ticker}...")

        df = client.get_dataframe(ticker)

        if df is not None and len(df) >= 250:
            # Calculate indicators if not present
            df = _ensure_indicators(df, client)
            ticker_data[ticker] = df
        else:
            if verbose:
                print(f"  Skipping {ticker}: insufficient data")

    return ticker_data


def _ensure_indicators(df: pd.DataFrame, client) -> pd.DataFrame:
    """Ensure all required indicators are calculated."""
    calc = client.calc

    # Calculate indicators if missing
    if 'RSI' not in df.columns:
        df['RSI'] = calc.rsi(df['close'])

    if 'MACD' not in df.columns:
        macd, signal, hist = calc.macd(df['close'])
        df['MACD'] = macd
        df['MACD_SIGNAL'] = signal
        df['MACD_HIST'] = hist

    if 'SMA_50' not in df.columns:
        df['SMA_50'] = calc.sma(df['close'], 50)

    if 'SMA_200' not in df.columns:
        df['SMA_200'] = calc.sma(df['close'], min(200, len(df)))

    if 'ADX' not in df.columns:
        df['ADX'] = calc.adx(df)

    return df


def run_backtest_cli(
    tickers: List[str],
    signal_type: SignalType = SignalType.UPSIDE_REVERSAL,
    conviction_filter: Optional[ConvictionLevel] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    api_key: Optional[str] = None,
    cache_dir: Optional[str] = None,
    output_csv: Optional[str] = None,
    detailed: bool = False,
    verbose: bool = False,
):
    """Run backtest from command line."""
    print(f"Loading data for {len(tickers)} tickers...")
    ticker_data = load_ticker_data(
        tickers, api_key, cache_dir, verbose
    )

    if not ticker_data:
        print("Error: No valid ticker data loaded.")
        return

    print(f"Loaded {len(ticker_data)} tickers with sufficient data.")
    print(f"Running backtest...")

    engine = BacktestEngine(verbose=verbose)
    result = engine.run_backtest(
        ticker_data=ticker_data,
        signal_type=signal_type,
        start_date=start_date,
        end_date=end_date,
        conviction_filter=conviction_filter,
    )

    # Generate report
    report = generate_backtest_report(result, detailed=detailed)
    print(report)

    # Export CSV if requested
    if output_csv:
        csv_data = generate_csv_report(result)
        with open(output_csv, 'w') as f:
            f.write(csv_data)
        print(f"\nCSV exported to: {output_csv}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run backtest on reversal signals"
    )

    parser.add_argument(
        '--tickers',
        type=str,
        help='Comma-separated list of ticker symbols'
    )

    parser.add_argument(
        '--ticker-file',
        type=str,
        help='File with ticker symbols (one per line)'
    )

    parser.add_argument(
        '--signal-type',
        choices=['upside', 'downside'],
        default='upside',
        help='Signal type to backtest'
    )

    parser.add_argument(
        '--conviction',
        choices=['high', 'medium', 'low'],
        help='Filter by minimum conviction level'
    )

    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        help='End date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--cache-dir',
        type=str,
        default='.cache',
        help='Cache directory for market data'
    )

    parser.add_argument(
        '--output-csv',
        type=str,
        help='Export signals to CSV file'
    )

    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Include detailed signal list'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Get tickers
    tickers = []
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(',')]
    elif args.ticker_file:
        with open(args.ticker_file) as f:
            tickers = [line.strip().upper() for line in f if line.strip()]
    else:
        print("Error: Must specify --tickers or --ticker-file")
        sys.exit(1)

    # Parse signal type
    signal_type = (
        SignalType.UPSIDE_REVERSAL if args.signal_type == 'upside'
        else SignalType.DOWNSIDE_REVERSAL
    )

    # Parse conviction filter
    conviction_filter = None
    if args.conviction:
        conviction_map = {
            'high': ConvictionLevel.HIGH,
            'medium': ConvictionLevel.MEDIUM,
            'low': ConvictionLevel.LOW,
        }
        conviction_filter = conviction_map[args.conviction]

    # Parse dates
    start_date = None
    end_date = None
    if args.start_date:
        start_date = date.fromisoformat(args.start_date)
    if args.end_date:
        end_date = date.fromisoformat(args.end_date)

    # Run backtest
    run_backtest_cli(
        tickers=tickers,
        signal_type=signal_type,
        conviction_filter=conviction_filter,
        start_date=start_date,
        end_date=end_date,
        cache_dir=args.cache_dir,
        output_csv=args.output_csv,
        detailed=args.detailed,
        verbose=args.verbose,
    )


if __name__ == '__main__':
    main()
