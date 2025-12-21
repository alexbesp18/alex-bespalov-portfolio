#!/usr/bin/env python3
"""
Run Transcripts - Fetch earnings transcripts with caching.

Features:
- Daily caching: API called at most once per ticker per day
- Grok AI summarization: Key metrics, guidance, tone, summary
- Days since earnings tracking

Usage:
    python run_transcripts.py
    python run_transcripts.py --verbose --dry-run
    python run_transcripts.py --limit 10 --batch-size 5
    python run_transcripts.py --force-refresh  # Ignore cache
"""

import argparse
import sys
import time
import datetime as dt
from pathlib import Path

from core import (
    load_config,
    DataCache,
    TranscriptClient,
    GrokAnalyzer,
    SheetManager,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Fetch earnings transcripts with caching'
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
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Check if defeatbeta is available
    if not TranscriptClient.is_available():
        print("❌ defeatbeta-api not installed. Cannot fetch transcripts.")
        print("   Install with: pip install defeatbeta-api duckdb")
        sys.exit(1)
    
    # Resolve config path
    script_dir = Path(__file__).parent
    config_path = script_dir / args.config
    if not config_path.exists():
        config_path = script_dir / 'config.json'
    
    if not config_path.exists():
        print(f"❌ Config file not found: {args.config}")
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
    print("TRANSCRIPTS LOADER (vFinal with caching)")
    print("=" * 60)
    
    # Initialize components
    data_dir = script_dir / 'data'
    cache = DataCache(data_dir, verbose=config.verbose)
    
    # Show cache stats
    stats = cache.get_cache_stats()
    print(f"\n📁 Cache: {stats['transcripts_today']} transcripts cached today")
    
    transcript_client = TranscriptClient(
        cache=cache,
        min_chars=config.defeatbeta.min_chars,
        earliest_year_offset=config.defeatbeta.earliest_year_offset,
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
    existing_tickers = []
    tickers_to_process = []
    
    if config.clean:
        print(f"   🧹 CLEAN RUN: Will overwrite all data")
        tickers_to_process = tickers
    elif config.force_refresh:
        print(f"   🔄 FORCE REFRESH: Ignoring cache")
        tickers_to_process = tickers
    else:
        # Check existing in sheet
        print(f"\n🔍 Checking existing data in '{config.google_sheets.transcripts_tab}'...")
        existing_tickers = sheet_manager.get_existing_tickers(config.google_sheets.transcripts_tab)
        
        if existing_tickers:
            print(f"   Found {len(existing_tickers)} existing tickers")
        
        # Find tickers needing refresh
        tickers_to_process = transcript_client.get_tickers_needing_refresh(tickers)
        
        # Also include any not in sheet
        for ticker in tickers:
            if ticker not in existing_tickers and ticker not in tickers_to_process:
                tickers_to_process.append(ticker)
    
    if not tickers_to_process:
        print("\n✅ All transcripts are cached!")
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
    print(f"\n📝 FETCHING TRANSCRIPTS")
    print("-" * 40)
    
    transcript_results = []
    for i, ticker in enumerate(tickers_to_process):
        is_cached = cache.get_transcript(ticker) is not None
        label = "📁 CACHED" if is_cached and not config.force_refresh else "🌐 FETCH"
        print(f"[{i+1}/{len(tickers_to_process)}] {label} {ticker}")
        
        result = transcript_client.fetch_transcript(
            ticker,
            force_refresh=config.force_refresh
        )
        
        if result and result.get('Status') == 'OK' and result.get('Full_Text'):
            # Summarize with Grok
            if grok:
                summary = grok.summarize_transcript(
                    ticker,
                    result.get('Period', 'N/A'),
                    result.get('Full_Text', '')
                )
                result.update(summary)
                time.sleep(0.3)
            
            # Remove full text (too long for sheet)
            result.pop('Full_Text', None)
        
        # Calculate days since earnings
        if result:
            earnings_date = result.get('Earnings_Date')
            days = transcript_client.calculate_days_since_earnings(earnings_date)
            result['Days_Since_Earnings'] = days if days is not None else 'N/A'
            result['Updated'] = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
            transcript_results.append(result)
        
        time.sleep(0.5)  # Be nice to defeatbeta
    
    # Write results
    if not config.dry_run:
        print(f"\n💾 WRITING TO GOOGLE SHEETS")
        print("-" * 40)
        
        should_append = len(existing_tickers) > 0 and not config.clean
        sheet_manager.write_transcripts(
            config.google_sheets.transcripts_tab,
            transcript_results,
            append=should_append
        )
    
    # Summary
    print(f"\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    
    trans_ok = sum(1 for r in transcript_results if r.get('Status') == 'OK')
    print(f"Transcripts: {trans_ok}/{len(tickers_to_process)} successful")
    
    if config.dry_run:
        print("\n⚠️  DRY RUN - No data was written to sheets")
    else:
        print(f"\n✅ Data written to tab: '{config.google_sheets.transcripts_tab}'")


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

