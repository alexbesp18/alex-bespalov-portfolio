#!/usr/bin/env python3
"""
Run All - Fetch both technical data and transcripts with caching.

This is the recommended entry point for the vFinal data loader.

Features:
- Daily caching: APIs called at most once per ticker per day
- Price monitoring: Tickers with >10% price move are refreshed
- Grok AI analysis for both technicals and transcripts
- Row replacement for updates

Usage:
    python run_all.py
    python run_all.py --verbose --dry-run
    python run_all.py --limit 10 --batch-size 5
    python run_all.py --force-refresh  # Ignore cache
    python run_all.py --clean          # Overwrite all data
"""

import argparse
import sys
import time
import datetime as dt
from pathlib import Path

from core import (
    load_config,
    DataCache,
    TwelveDataClient,
    TranscriptClient,
    GrokAnalyzer,
    SheetManager,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Fetch technical data and transcripts with caching'
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
    parser.add_argument('--technicals-only', action='store_true',
                        help='Skip transcripts, only fetch technicals')
    parser.add_argument('--transcripts-only', action='store_true',
                        help='Skip technicals, only fetch transcripts')
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Resolve config path
    script_dir = Path(__file__).parent
    config_path = script_dir / args.config
    if not config_path.exists():
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
    
    # Determine what to run
    run_technicals = not args.transcripts_only
    run_transcripts = not args.technicals_only and TranscriptClient.is_available()
    
    if args.transcripts_only and not TranscriptClient.is_available():
        print("❌ defeatbeta-api not installed. Cannot fetch transcripts.")
        print("   Install with: pip install defeatbeta-api duckdb")
        sys.exit(1)
    
    mode = "TECHNICALS + TRANSCRIPTS"
    if args.technicals_only:
        mode = "TECHNICALS ONLY"
    elif args.transcripts_only:
        mode = "TRANSCRIPTS ONLY"
    elif not TranscriptClient.is_available():
        mode = "TECHNICALS ONLY (defeatbeta not installed)"
    
    print("\n" + "=" * 60)
    print(f"DATA LOADER (vFinal) - {mode}")
    print("=" * 60)
    
    # Initialize components
    data_dir = script_dir / 'data'
    cache = DataCache(data_dir, verbose=config.verbose)
    
    if args.clear_cache:
        deleted = cache.clear_old_cache(days=7)
        print(f"   🗑️  Cleared {deleted} old cache files")
    
    # Show cache stats
    stats = cache.get_cache_stats()
    print(f"\n📁 Cache: {stats['twelve_data_today']} technicals, "
          f"{stats['transcripts_today']} transcripts cached today "
          f"({stats['total_size_mb']}MB total)")
    
    # Initialize clients
    twelve_data = TwelveDataClient(
        api_key=config.twelve_data.api_key,
        cache=cache,
        output_size=config.twelve_data.output_size,
        rate_limit_sleep=config.twelve_data.rate_limit_sleep,
        verbose=config.verbose,
    ) if run_technicals else None
    
    transcript_client = TranscriptClient(
        cache=cache,
        min_chars=config.defeatbeta.min_chars,
        earliest_year_offset=config.defeatbeta.earliest_year_offset,
        verbose=config.verbose,
    ) if run_transcripts else None
    
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
    existing_tech_data = {}
    existing_transcript_tickers = []
    
    if not config.clean and not config.force_refresh:
        if run_technicals:
            print(f"\n🔍 Checking existing technical data...")
            existing_tech_data = sheet_manager.get_existing_tech_data(config.google_sheets.tech_data_tab)
            if existing_tech_data:
                print(f"   Found {len(existing_tech_data)} existing tickers")
        
        if run_transcripts:
            print(f"🔍 Checking existing transcripts...")
            existing_transcript_tickers = sheet_manager.get_existing_tickers(config.google_sheets.transcripts_tab)
            if existing_transcript_tickers:
                print(f"   Found {len(existing_transcript_tickers)} existing tickers")
    
    # Find tickers needing processing
    if config.clean or config.force_refresh:
        tickers_for_tech = tickers if run_technicals else []
        tickers_for_trans = tickers if run_transcripts else []
        if config.clean:
            print(f"   🧹 CLEAN RUN: Will overwrite all data")
        else:
            print(f"   🔄 FORCE REFRESH: Ignoring cache")
    else:
        # Technicals: check cache for today
        if run_technicals:
            tickers_for_tech = twelve_data.get_tickers_needing_refresh(tickers)
            # Add tickers not in sheet
            for ticker in tickers:
                if ticker not in existing_tech_data and ticker not in tickers_for_tech:
                    tickers_for_tech.append(ticker)
        else:
            tickers_for_tech = []
        
        # Transcripts: check cache only
        if run_transcripts:
            tickers_for_trans = transcript_client.get_tickers_needing_refresh(tickers)
            for ticker in tickers:
                if ticker not in existing_transcript_tickers and ticker not in tickers_for_trans:
                    tickers_for_trans.append(ticker)
        else:
            tickers_for_trans = []
    
    # Apply limits (use union of both lists)
    all_tickers_to_process = list(dict.fromkeys(tickers_for_tech + tickers_for_trans))
    
    if not all_tickers_to_process:
        print("\n✅ All data is cached and up to date!")
        print("   Use --force-refresh to fetch fresh data anyway.")
        return
    
    if config.limit > 0:
        all_tickers_to_process = all_tickers_to_process[:config.limit]
        print(f"   ⚠️  LIMITING to {config.limit} tickers")
    
    if config.batch_size > 0 and len(all_tickers_to_process) > config.batch_size:
        all_tickers_to_process = all_tickers_to_process[:config.batch_size]
        print(f"   📦 BATCH MODE: Processing {config.batch_size} tickers")
    
    # Filter tech and trans lists to only include tickers we're processing
    tickers_for_tech = [t for t in tickers_for_tech if t in all_tickers_to_process]
    tickers_for_trans = [t for t in tickers_for_trans if t in all_tickers_to_process]
    
    print(f"\n🚀 Processing: {len(tickers_for_tech)} technicals, {len(tickers_for_trans)} transcripts")
    
    # =========================================================================
    # TECHNICALS
    # =========================================================================
    
    tech_results = []
    if run_technicals and tickers_for_tech:
        print(f"\n📊 FETCHING TECHNICAL DATA")
        print("-" * 40)
        
        for i, ticker in enumerate(tickers_for_tech):
            is_cached = cache.get_twelve_data(ticker) is not None
            label = "📁" if is_cached and not config.force_refresh else "🌐"
            print(f"[{i+1}/{len(tickers_for_tech)}] {label} {ticker}")
            
            result = twelve_data.fetch_and_calculate(ticker, force_refresh=config.force_refresh)
            
            if result and result.get('Status') == 'OK':
                if grok:
                    ai_analysis = grok.analyze_technicals(ticker, result)
                    result.update(ai_analysis)
                    time.sleep(0.3)
                tech_results.append(result)
            elif result:
                tech_results.append(result)
            
            if not is_cached or config.force_refresh:
                time.sleep(config.twelve_data.rate_limit_sleep)
    
    # =========================================================================
    # TRANSCRIPTS
    # =========================================================================
    
    transcript_results = []
    if run_transcripts and tickers_for_trans:
        print(f"\n📝 FETCHING TRANSCRIPTS")
        print("-" * 40)
        
        for i, ticker in enumerate(tickers_for_trans):
            is_cached = cache.get_transcript(ticker) is not None
            label = "📁" if is_cached and not config.force_refresh else "🌐"
            print(f"[{i+1}/{len(tickers_for_trans)}] {label} {ticker}")
            
            result = transcript_client.fetch_transcript(ticker, force_refresh=config.force_refresh)
            
            if result and result.get('Status') == 'OK' and result.get('Full_Text'):
                if grok:
                    summary = grok.summarize_transcript(
                        ticker, result.get('Period', 'N/A'), result.get('Full_Text', '')
                    )
                    result.update(summary)
                    time.sleep(0.3)
                result.pop('Full_Text', None)
            
            if result:
                earnings_date = result.get('Earnings_Date')
                days = transcript_client.calculate_days_since_earnings(earnings_date)
                result['Days_Since_Earnings'] = days if days is not None else 'N/A'
                result['Updated'] = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
                transcript_results.append(result)
            
            time.sleep(0.5)
    
    # =========================================================================
    # WRITE RESULTS
    # =========================================================================
    
    if not config.dry_run:
        print(f"\n💾 WRITING TO GOOGLE SHEETS")
        print("-" * 40)
        
        if tech_results:
            if config.clean or not existing_tech_data:
                sheet_manager.write_tech_data(
                    config.google_sheets.tech_data_tab, tech_results, append=False
                )
            else:
                sheet_manager.write_tech_data_with_replacements(
                    config.google_sheets.tech_data_tab, tech_results, existing_tech_data
                )
        
        if transcript_results:
            should_append = len(existing_transcript_tickers) > 0 and not config.clean
            sheet_manager.write_transcripts(
                config.google_sheets.transcripts_tab, transcript_results, append=should_append
            )

        # Archive technicals to Supabase (with Grok analysis)
        if tech_results:
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
    
    if tech_results:
        tech_ok = sum(1 for r in tech_results if r.get('Status') == 'OK')
        print(f"Technical data: {tech_ok}/{len(tickers_for_tech)} successful")
    
    if transcript_results:
        trans_ok = sum(1 for r in transcript_results if r.get('Status') == 'OK')
        print(f"Transcripts:    {trans_ok}/{len(tickers_for_trans)} successful")
    
    if config.dry_run:
        print("\n⚠️  DRY RUN - No data was written to sheets")
    else:
        tabs = []
        if tech_results:
            tabs.append(f"'{config.google_sheets.tech_data_tab}'")
        if transcript_results:
            tabs.append(f"'{config.google_sheets.transcripts_tab}'")
        if tabs:
            print(f"\n✅ Data written to: {' and '.join(tabs)}")


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

