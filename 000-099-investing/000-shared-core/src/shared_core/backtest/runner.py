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
from datetime import date
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .engine import BacktestEngine
from .models import SignalType, ConvictionLevel
from .report import generate_backtest_report, generate_csv_report


def find_cached_files(cache_dir: str, ticker: str) -> Optional[Path]:
    """
    Find the most recent cache file for a ticker.

    Handles both JSON (TICKER_DATE.json) and parquet formats.
    """
    cache_path = Path(cache_dir)
    twelve_data_dir = cache_path / "twelve_data"

    if not twelve_data_dir.exists():
        return None

    # Look for JSON files first (primary format)
    json_files = sorted(twelve_data_dir.glob(f"{ticker.upper()}_*.json"), reverse=True)
    if json_files:
        return json_files[0]

    # Fall back to parquet
    parquet_files = sorted(twelve_data_dir.glob(f"{ticker.upper()}.parquet"), reverse=True)
    if parquet_files:
        return parquet_files[0]

    return None


def load_from_cache(cache_dir: str, tickers: List[str], verbose: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Load ticker data directly from cache files.

    This is faster than going through the TwelveDataClient when we just want cached data.
    """
    ticker_data = {}
    cache_path = Path(cache_dir)
    twelve_data_dir = cache_path / "twelve_data"

    if not twelve_data_dir.exists():
        if verbose:
            print(f"Cache directory not found: {twelve_data_dir}")
        return ticker_data

    for ticker in tickers:
        cache_file = find_cached_files(cache_dir, ticker)

        if cache_file is None:
            if verbose:
                print(f"  {ticker}: No cache file found")
            continue

        try:
            if cache_file.suffix == '.json':
                df = pd.read_json(cache_file)
            elif cache_file.suffix == '.parquet':
                df = pd.read_parquet(cache_file)
            else:
                continue

            if len(df) >= 250:
                ticker_data[ticker] = df
                if verbose:
                    print(f"  {ticker}: Loaded {len(df)} days from cache")
            else:
                if verbose:
                    print(f"  {ticker}: Insufficient data ({len(df)} days)")

        except Exception as e:
            if verbose:
                print(f"  {ticker}: Error loading cache - {e}")

    return ticker_data


def get_all_cached_tickers(cache_dir: str) -> List[str]:
    """Get list of all tickers available in cache."""
    cache_path = Path(cache_dir)
    twelve_data_dir = cache_path / "twelve_data"

    if not twelve_data_dir.exists():
        return []

    tickers = set()

    # Find JSON files
    for f in twelve_data_dir.glob("*_*.json"):
        # Extract ticker from TICKER_DATE.json format
        ticker = f.stem.rsplit('_', 1)[0]
        tickers.add(ticker.upper())

    # Find parquet files
    for f in twelve_data_dir.glob("*.parquet"):
        tickers.add(f.stem.upper())

    return sorted(tickers)


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

    # Try loading from cache first
    if cache_dir:
        if verbose:
            print(f"Loading from cache: {cache_dir}")
        ticker_data = load_from_cache(cache_dir, tickers, verbose)

        # Calculate indicators for cached data
        if ticker_data:
            # Need a client just for indicator calculation
            client = TwelveDataClient(api_key="", output_size=1000, verbose=False)
            for ticker, df in ticker_data.items():
                ticker_data[ticker] = _ensure_indicators(df, client)

        # Check which tickers we still need
        missing_tickers = [t for t in tickers if t not in ticker_data]

        if not missing_tickers:
            return ticker_data

        if verbose and missing_tickers:
            print(f"Missing from cache: {', '.join(missing_tickers[:10])}...")
    else:
        ticker_data = {}
        missing_tickers = tickers

    # Get API key for missing tickers
    if not api_key:
        api_key = os.environ.get('TWELVE_DATA_API_KEY')

    if not api_key and missing_tickers:
        if verbose:
            print("Warning: No API key provided. Using cached data only.")
        return ticker_data

    # Fetch missing tickers from API
    if missing_tickers and api_key:
        cache = DataCache(cache_dir, verbose=verbose) if cache_dir else None
        client = TwelveDataClient(
            api_key=api_key,
            cache=cache,
            output_size=1000,
            verbose=verbose,
        )

        for ticker in missing_tickers:
            if verbose:
                print(f"Fetching {ticker} from API...")

            df = client.get_dataframe(ticker)

            if df is not None and len(df) >= 250:
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
    print("Running backtest...")

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
