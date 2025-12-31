#!/usr/bin/env python3
"""
Run Covariance - Compute correlation/covariance matrix from cached price data.

This script uses ONLY cached data (no API calls). It finds the most recent
cache file for each ticker and builds a full correlation matrix for portfolio analysis.

Usage:
    python run_covariance.py                    # Default: correlation matrix
    python run_covariance.py --type covariance  # Covariance matrix instead
    python run_covariance.py --period 60        # Use last 60 days only
    python run_covariance.py --dry-run          # Preview without writing to sheets
    python run_covariance.py --min-days 100     # Require 100+ days of data per ticker
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict
import datetime as dt

import pandas as pd
import numpy as np

from core import load_config, SheetManager


def parse_args():
    parser = argparse.ArgumentParser(
        description='Compute correlation/covariance matrix from cached price data'
    )
    parser.add_argument('--config', '-c', default='config.json',
                        help='Path to configuration file (default: config.json)')
    parser.add_argument('--type', '-t', choices=['correlation', 'covariance'],
                        default='correlation',
                        help='Type of matrix to compute (default: correlation)')
    parser.add_argument('--period', '-p', type=int, default=0,
                        help='Use only last N days of data (0 = all available)')
    parser.add_argument('--min-days', type=int, default=50,
                        help='Minimum days of data required per ticker (default: 50)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Compute matrix but do not write to sheets')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print detailed progress')
    parser.add_argument('--output-csv', type=str, default='',
                        help='Also save matrix to CSV file')
    return parser.parse_args()


def find_latest_cache_files(cache_dir: Path) -> dict:
    """
    Find the most recent cache file for each ticker.
    
    Returns:
        Dict mapping ticker -> Path to most recent cache file
    """
    ticker_files = defaultdict(list)
    
    for f in cache_dir.glob('*.json'):
        # Parse filename: TICKER_YYYY-MM-DD.json
        parts = f.stem.rsplit('_', 1)
        if len(parts) != 2:
            continue
        
        ticker, date_str = parts
        try:
            file_date = dt.date.fromisoformat(date_str)
            ticker_files[ticker].append((file_date, f))
        except ValueError:
            continue
    
    # Keep only the most recent file per ticker
    latest = {}
    for ticker, files in ticker_files.items():
        files.sort(key=lambda x: x[0], reverse=True)
        latest[ticker] = files[0][1]  # Most recent file path
    
    return latest


def load_price_data(cache_files: dict, min_days: int, verbose: bool) -> pd.DataFrame:
    """
    Load price data from cache files into a unified DataFrame.
    
    Returns:
        DataFrame with dates as index, tickers as columns, close prices as values
    """
    prices = {}
    skipped = []
    
    for ticker, filepath in sorted(cache_files.items()):
        try:
            df = pd.read_json(filepath)
            
            # Ensure we have required columns
            if 'close' not in df.columns:
                skipped.append((ticker, 'no close column'))
                continue
            
            if len(df) < min_days:
                skipped.append((ticker, f'only {len(df)} days'))
                continue
            
            # Handle datetime column
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
                df = df.set_index('datetime')
            
            prices[ticker] = df['close']
            
        except Exception as e:
            skipped.append((ticker, str(e)[:30]))
            continue
    
    if verbose and skipped:
        print(f"\n⚠️  Skipped {len(skipped)} tickers:")
        for ticker, reason in skipped[:10]:
            print(f"   {ticker}: {reason}")
        if len(skipped) > 10:
            print(f"   ... and {len(skipped) - 10} more")
    
    if not prices:
        return pd.DataFrame()
    
    # Combine into single DataFrame
    price_matrix = pd.DataFrame(prices)
    price_matrix = price_matrix.sort_index()
    
    return price_matrix


def compute_matrix(returns: pd.DataFrame, matrix_type: str) -> pd.DataFrame:
    """
    Compute correlation or covariance matrix.
    """
    if matrix_type == 'correlation':
        return returns.corr()
    else:
        return returns.cov()


def write_to_sheets(sheet_manager: SheetManager, matrix: pd.DataFrame, 
                    tab_name: str, verbose: bool) -> None:
    """
    Write matrix to Google Sheets.
    """
    try:
        sheet = sheet_manager.spreadsheet.worksheet(tab_name)
        sheet.clear()
    except Exception:
        sheet = sheet_manager.spreadsheet.add_worksheet(
            title=tab_name, rows=len(matrix) + 5, cols=len(matrix) + 5
        )
    
    # Prepare data with headers
    tickers = matrix.columns.tolist()
    
    # Header row
    rows = [[''] + tickers]
    
    # Data rows
    for ticker in tickers:
        row = [ticker] + [round(matrix.loc[ticker, col], 4) for col in tickers]
        rows.append(row)
    
    # Write to sheet
    sheet.update(rows, 'A1')
    
    if verbose:
        print(f"   ✅ Wrote {len(tickers)}×{len(tickers)} matrix to '{tab_name}'")


def main():
    args = parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    cache_dir = script_dir / 'data' / 'twelve_data'
    
    config_path = script_dir / args.config
    if not config_path.exists():
        config_path = script_dir / 'config.json'
    
    print("\n" + "=" * 60)
    print(f"COVARIANCE MATRIX (cache-only mode)")
    print("=" * 60)
    
    # Check cache directory
    if not cache_dir.exists():
        print(f"\n❌ Cache directory not found: {cache_dir}")
        print("   Run run_technicals.py first to populate the cache.")
        sys.exit(1)
    
    # Find latest cache files
    print(f"\n📁 Scanning cache directory...")
    cache_files = find_latest_cache_files(cache_dir)
    
    if not cache_files:
        print(f"\n❌ No cached data found in {cache_dir}")
        print("   Run run_technicals.py first to populate the cache.")
        sys.exit(1)
    
    print(f"   Found {len(cache_files)} tickers with cached data")
    
    # Show date range of cached data
    dates = []
    for f in cache_files.values():
        date_str = f.stem.rsplit('_', 1)[1]
        dates.append(date_str)
    unique_dates = sorted(set(dates))
    if len(unique_dates) == 1:
        print(f"   Cache date: {unique_dates[0]}")
    else:
        print(f"   Cache dates: {unique_dates[0]} to {unique_dates[-1]}")
    
    # Load price data
    print(f"\n📊 Loading price data (min {args.min_days} days required)...")
    price_matrix = load_price_data(cache_files, args.min_days, args.verbose)
    
    if price_matrix.empty:
        print(f"\n❌ No valid price data found")
        sys.exit(1)
    
    print(f"   Loaded {len(price_matrix.columns)} tickers × {len(price_matrix)} days")
    
    # Apply period filter
    if args.period > 0:
        price_matrix = price_matrix.tail(args.period)
        print(f"   Filtered to last {args.period} days: {len(price_matrix)} rows")
    
    # Drop tickers with too many NaN values (require 80% coverage)
    min_valid = int(len(price_matrix) * 0.8)
    valid_cols = price_matrix.columns[price_matrix.notna().sum() >= min_valid]
    dropped = len(price_matrix.columns) - len(valid_cols)
    if dropped > 0:
        print(f"   Dropped {dropped} tickers with insufficient data overlap")
        price_matrix = price_matrix[valid_cols]
    
    # Calculate returns
    print(f"\n📈 Computing daily returns...")
    returns = price_matrix.pct_change().dropna()
    print(f"   Returns matrix: {len(returns)} days × {len(returns.columns)} tickers")
    
    # Compute matrix
    matrix_type = args.type
    print(f"\n🔢 Computing {matrix_type} matrix...")
    matrix = compute_matrix(returns, matrix_type)
    print(f"   Result: {len(matrix)}×{len(matrix)} matrix")
    
    # Summary stats for correlation
    if matrix_type == 'correlation':
        # Get upper triangle (excluding diagonal)
        upper = matrix.where(np.triu(np.ones(matrix.shape), k=1).astype(bool))
        flat = upper.stack()
        print(f"\n📊 Correlation Summary:")
        print(f"   Mean:   {flat.mean():.3f}")
        print(f"   Median: {flat.median():.3f}")
        print(f"   Min:    {flat.min():.3f}")
        print(f"   Max:    {flat.max():.3f}")
    
    # Save to CSV if requested
    if args.output_csv:
        matrix.to_csv(args.output_csv)
        print(f"\n💾 Saved to: {args.output_csv}")
    
    # Write to Google Sheets
    if not args.dry_run:
        print(f"\n💾 Writing to Google Sheets...")
        
        try:
            config = load_config(str(config_path))
            sheet_manager = SheetManager(
                credentials_file=str(script_dir / config.google_sheets.credentials_file),
                spreadsheet_name=config.google_sheets.spreadsheet_name,
                verbose=args.verbose,
            )
            
            tab_name = "Correlation" if matrix_type == 'correlation' else "Covariance"
            write_to_sheets(sheet_manager, matrix, tab_name, args.verbose)
            
            print(f"\n✅ Matrix written to tab: '{tab_name}'")
            
        except Exception as e:
            print(f"\n❌ Error writing to sheets: {e}")
            print("   You can still use --output-csv to save locally")
            sys.exit(1)
    else:
        print(f"\n⚠️  DRY RUN - Matrix not written to sheets")
        print(f"   Preview (first 5×5):")
        print(matrix.iloc[:5, :5].round(3).to_string())
    
    # Summary
    print(f"\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"Matrix size: {len(matrix)}×{len(matrix)} ({len(matrix)**2:,} cells)")
    print(f"Unique pairs: {len(matrix) * (len(matrix) - 1) // 2:,}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

