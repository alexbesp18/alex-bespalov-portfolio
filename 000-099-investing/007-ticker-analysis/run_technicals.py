#!/usr/bin/env python3
"""
Run Technicals - Fetch technical data with caching and price monitoring.

Features:
- Daily caching: API called at most once per ticker per day
- Price monitoring: Tickers with >10% price move are refreshed
- Row replacement: Updates existing rows instead of just appending
- Grok AI analysis: Tech_Summary with detailed breakdown

Usage:
    python run_technicals.py
    python run_technicals.py --verbose --dry-run
    python run_technicals.py --limit 10 --batch-size 5
    python run_technicals.py --force-refresh  # Ignore cache
    python run_technicals.py --clean          # Overwrite all data
"""

import argparse
import sys
import time
from pathlib import Path

from core import (
    load_config,
    DataCache,
    TwelveDataClient,
    GrokAnalyzer,
    SheetManager,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Fetch technical data with caching and price monitoring'
    )
    parser.add_argument('--config', '-c', default='config.json',
                        help='Path to configuration file (default: config.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print detailed progress information')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Fetch data but do not write to sheets')
    parser.add_argument('--limit', '-l', type=int, default=0,
                        help='Limit the number of tickers to process (0 = all)')
    parser.add_argument('--batch-size', '-b', type=int, default=0,
                        help='Batch size: process N tickers then stop')
    parser.add_argument('--clean', action='store_true',
                        help='Start fresh: ignore existing data and overwrite sheets')
    parser.add_argument('--force-refresh', action='store_true',
                        help='Bypass cache and fetch fresh data for all tickers')
    parser.add_argument('--clear-cache', action='store_true',
                        help='Clear old cache files (>7 days) before running')
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Resolve config path
    script_dir = Path(__file__).parent
    config_path = script_dir / args.config
    if not config_path.exists():
        # Try parent directory
        config_path = script_dir / 'config.json'
    
    if not config_path.exists():
        print(f"❌ Config file not found: {args.config}")
        print(f"   Create config.json or specify path with --config")
        sys.exit(1)
    
    # Load configuration
    try:
        config = load_config(
            str(config_path),
            verbose=args.verbose,
            dry_run=args.dry_run,
            limit=args.limit,
            batch_size=args.batch_size,
            clean=args.clean,
            force_refresh=args.force_refresh,
        )
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("TECHNICALS LOADER (vFinal with caching)")
    print("=" * 60)
    
    # Initialize components
    data_dir = script_dir / 'data'
    cache = DataCache(data_dir, verbose=config.verbose)
    
    if args.clear_cache:
        deleted = cache.clear_old_cache(days=7)
        print(f"   🗑️  Cleared {deleted} old cache files")
    
    # Show cache stats
    stats = cache.get_cache_stats()
    print(f"\n📁 Cache: {stats['twelve_data_today']} tickers cached today, "
          f"{stats['total_size_mb']}MB total")
    
    twelve_data = TwelveDataClient(
        api_key=config.twelve_data.api_key,
        cache=cache,
        output_size=config.twelve_data.output_size,
        rate_limit_sleep=config.twelve_data.rate_limit_sleep,
        verbose=config.verbose,
    )
    
    grok = GrokAnalyzer(
        api_key=config.grok.api_key,
        model=config.grok.model,
        max_tokens=config.grok.max_summary_tokens,
        verbose=config.verbose,
    ) if config.grok.summarization_enabled else None
    
    sheet_manager = SheetManager(
        credentials_file=str(script_dir / config.google_sheets.credentials_file),
        spreadsheet_name=config.google_sheets.spreadsheet_name,
        verbose=config.verbose,
    )
    
    # Get tickers from main sheet
    print(f"\n📋 Reading tickers from '{config.google_sheets.main_tab}'...")
    tickers = sheet_manager.get_tickers(
        config.google_sheets.main_tab,
        config.google_sheets.ticker_column,
        config.google_sheets.start_row,
    )
    
    if not tickers:
        print("❌ No tickers found!")
        return
    
    print(f"   Found {len(tickers)} tickers: {', '.join(tickers[:10])}{'...' if len(tickers) > 10 else ''}")
    
    # Determine which tickers need processing
    existing_data = {}
    tickers_to_process = []
    
    if config.clean:
        print(f"   🧹 CLEAN RUN: Will overwrite all data")
        tickers_to_process = tickers
    elif config.force_refresh:
        print(f"   🔄 FORCE REFRESH: Ignoring cache")
        tickers_to_process = tickers
    else:
        # Get existing data for price comparison
        print(f"\n🔍 Checking existing data in '{config.google_sheets.tech_data_tab}'...")
        existing_data = sheet_manager.get_existing_tech_data(config.google_sheets.tech_data_tab)
        
        if existing_data:
            print(f"   Found {len(existing_data)} existing tickers")
        
        # Find tickers needing refresh (no cache for today)
        tickers_to_process = twelve_data.get_tickers_needing_refresh(tickers)
        
        # Also include any tickers not in the sheet yet
        sheet_tickers = set(existing_data.keys())
        for ticker in tickers:
            if ticker not in sheet_tickers and ticker not in tickers_to_process:
                tickers_to_process.append(ticker)
    
    if not tickers_to_process:
        print("\n✅ All tickers are cached for today!")
        print("   Use --force-refresh to fetch fresh data anyway.")
        return
    
    # Apply limits
    if config.limit > 0:
        tickers_to_process = tickers_to_process[:config.limit]
        print(f"   ⚠️  LIMITING to {config.limit} tickers")
    
    if config.batch_size > 0 and len(tickers_to_process) > config.batch_size:
        tickers_to_process = tickers_to_process[:config.batch_size]
        print(f"   📦 BATCH MODE: Processing {config.batch_size} tickers")
    
    print(f"\n🚀 Processing {len(tickers_to_process)} tickers...")
    
    # Fetch and process
    print(f"\n📊 FETCHING TECHNICAL DATA")
    print("-" * 40)
    
    tech_results = []
    for i, ticker in enumerate(tickers_to_process):
        is_cached = cache.get_twelve_data(ticker) is not None
        label = "📁 CACHED" if is_cached and not config.force_refresh else "🌐 FETCH"
        print(f"[{i+1}/{len(tickers_to_process)}] {label} {ticker}")
        
        result = twelve_data.fetch_and_calculate(
            ticker, 
            force_refresh=config.force_refresh
        )
        
        if result and result.get('Status') == 'OK':
            # Add Grok analysis
            if grok:
                ai_analysis = grok.analyze_technicals(ticker, result)
                result.update(ai_analysis)
                time.sleep(0.3)  # Rate limit Grok calls
            
            tech_results.append(result)
        elif result:
            tech_results.append(result)  # Include errors
        
        # Rate limit between API calls (only if we actually called API)
        if not is_cached or config.force_refresh:
            time.sleep(config.twelve_data.rate_limit_sleep)
    
    # Write results
    if not config.dry_run:
        print(f"\n💾 WRITING TO GOOGLE SHEETS")
        print("-" * 40)

        if config.clean or not existing_data:
            sheet_manager.write_tech_data(
                config.google_sheets.tech_data_tab,
                tech_results,
                append=False
            )
        else:
            sheet_manager.write_tech_data_with_replacements(
                config.google_sheets.tech_data_tab,
                tech_results,
                existing_data
            )

        # Archive to Supabase (with Grok analysis)
        print(f"\n💾 ARCHIVING TO SUPABASE")
        print("-" * 40)
        try:
            from shared_core.archive import archive_daily_indicators

            # Map tech_results to archive format
            archive_data = []
            for r in tech_results:
                if r.get('Status') != 'OK':
                    continue
                archive_data.append({
                    'symbol': r.get('Ticker'),
                    'close': r.get('Close'),
                    'rsi': r.get('RSI'),
                    'macd': r.get('MACD'),
                    'macd_signal': r.get('MACD_Signal'),
                    'macd_hist': r.get('MACD_Hist'),
                    'sma_20': r.get('SMA_20'),
                    'sma_50': r.get('SMA_50'),
                    'sma_200': r.get('SMA_200'),
                    'adx': r.get('ADX'),
                    'atr': r.get('ATR'),
                    'bb_upper': r.get('BB_Upper'),
                    'bb_lower': r.get('BB_Lower'),
                    'volume': r.get('Volume'),
                    'obv': r.get('OBV'),
                    'stoch_k': r.get('Stoch_K'),
                    'stoch_d': r.get('Stoch_D'),
                    # Grok analysis
                    'bullish_score': r.get('Bullish_Score'),
                    'bullish_reason': r.get('Bullish_Reason'),
                    'tech_summary': r.get('Tech_Summary'),
                })

            if archive_data:
                archived = archive_daily_indicators(archive_data, score_type="bullish")
                print(f"   ✅ Archived {archived} records to Supabase")
            else:
                print(f"   ⚠️  No valid data to archive")
        except ImportError:
            print(f"   ⚠️  shared_core not installed, skipping Supabase archive")
        except Exception as e:
            print(f"   ⚠️  Supabase archive failed: {e}")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    
    tech_ok = sum(1 for r in tech_results if r.get('Status') == 'OK')
    print(f"Technical data: {tech_ok}/{len(tickers_to_process)} successful")
    
    if config.dry_run:
        print("\n⚠️  DRY RUN - No data was written to sheets")
    else:
        print(f"\n✅ Data written to tab: '{config.google_sheets.tech_data_tab}'")


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

