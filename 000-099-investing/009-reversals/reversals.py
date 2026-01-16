import os
import argparse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Use shared_core utilities
from shared_core import (
    setup_logging,
    get_cached_tickers,
    get_latest_cached_tickers,
    check_time_guard,
    safe_read_json,
    StateManager,
    ArchiveManager,
    Digest,
    archive_daily_indicators,
)

from src.fetcher import TwelveDataFetcher
from src.calculator import TechnicalCalculator
from src.reversal_calculator import ReversalCalculator
from src.triggers import TriggerEngine
from src.notifier import Notifier

# Configure Logging using shared_core
logger = setup_logging("REVERSALS")


def load_watchlist(path):
    """Load watchlist from JSON file using shared_core utility."""
    return safe_read_json(path) or {}


def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Reversals Daily Scan - Mid-term Reversal Tracker")
    parser.add_argument("--dry-run", action="store_true", help="Do not send email")
    parser.add_argument("--reminder", action="store_true", help="Send 8am reminder based on last emailed digest (no data fetch)")
    parser.add_argument("--archive", type=str, default=None, help="Archive executed alerts: SYMBOL or SYMBOL:TRIGGER_KEY")
    parser.add_argument("--archive-days", type=int, default=30, help="Days to suppress archived alerts (default: 30)")
    parser.add_argument("--expected-local-hour", type=int, default=None, help="If set, only run when local time matches this hour")
    parser.add_argument("--expected-tz", type=str, default="America/Chicago", help="IANA timezone name used with --expected-local-hour")
    args = parser.parse_args()

    # Optional time guard using shared_core utility
    if args.expected_local_hour is not None:
        if not check_time_guard(args.expected_local_hour, args.expected_tz):
            return

    # Load Config
    base_dir = os.path.dirname(os.path.abspath(__file__))
    watchlist = load_watchlist(os.path.join(base_dir, "config/watchlist.json"))
    
    # Default cache location (007-ticker-analysis)
    cache_dir = os.path.join(base_dir, "..", "007-ticker-analysis", "data", "twelve_data")

    # State (prevents repeated alerts)
    state_path = os.path.join(base_dir, "data", "state.json")
    state_manager = StateManager(state_path)
    state = state_manager.load()
    last_run_trigger_keys = set(state_manager.get_last_run_trigger_keys(state))

    # Archive (suppresses alerts you've already acted on)
    archive_path = os.path.join(base_dir, "data", "archive.json")
    archive_manager = ArchiveManager(archive_path)
    archive = archive_manager.load()
    
    # Extract default triggers and tickers
    # Priority: 1) JSON config if has tickers, 2) cached data from 007-ticker-analysis
    default_triggers = watchlist.get('default_triggers', [])
    config_tickers = watchlist.get('tickers', [])
    
    if config_tickers:
        # Use JSON config (custom override)
        tickers = config_tickers
        logger.info(f"Using JSON config: {len(tickers)} tickers")
    else:
        # Default: use cached tickers from 007-ticker-analysis
        # Use lookback to handle UTC/EST timezone mismatch in cache file dates
        cached_symbols = get_latest_cached_tickers(cache_dir, lookback_days=3)
        # Convert to format expected by the rest of the code
        tickers = [{'symbol': s, 'theme': 'Cached'} for s in cached_symbols]
        logger.info(f"Using cached tickers from 007-ticker-analysis: {len(tickers)} tickers")

    # Initialize Components
    td_api_key = os.environ.get("TWELVE_DATA_API_KEY")
    resend_api_key = os.environ.get("RESEND_API_KEY")
    email_from = os.environ.get("SENDER_EMAIL")
    email_to_str = os.environ.get("NOTIFICATION_EMAILS", "")
    email_to = [e.strip() for e in email_to_str.split(",") if e.strip()]

    # Archive mode: mark last-digest triggers as executed/suppressed.
    if args.archive:
        target = args.archive.strip()
        symbol = target
        trigger_key = None
        if ":" in target:
            symbol, trigger_key = target.split(":", 1)
            symbol, trigger_key = symbol.strip(), trigger_key.strip()

        last_digest = state.get("last_digest") or {}
        digest_results = last_digest.get("results") or []
        archived_any = False

        for r in digest_results:
            if r.get("symbol") != symbol:
                continue
            keys = r.get("trigger_keys") or []
            msgs = r.get("triggers") or []
            for k, m in zip(keys, msgs):
                if trigger_key and k != trigger_key:
                    continue
                archive_manager.archive_trigger(
                    archive=archive,
                    symbol=symbol,
                    trigger_key=k,
                    trigger_message=m,
                    suppress_days=args.archive_days,
                )
                archived_any = True

        if not archived_any:
            logger.warning(
                "Archive: no matching triggers found in last digest. "
                "Run this after a main email, and use SYMBOL or SYMBOL:TRIGGER_KEY."
            )
        else:
            archive_manager.save(archive)
            logger.info(f"Archived {symbol}{(':' + trigger_key) if trigger_key else ''} for {args.archive_days} days.")
        return

    # Reminder mode: send based on the last digest, without fetching market data.
    if args.reminder:
        notifier = Notifier(resend_api_key, email_from, email_to)
        if not state_manager.should_send_reminder(state):
            logger.info("Reminder: no recent digest with triggers to remind on. Skipping.")
            return
        last_digest = state.get("last_digest") or {}
        digest_id = last_digest.get("digest_id") or datetime.utcnow().strftime("%Y-%m-%d")
        results = last_digest.get("results") or []
        body, buy_count, sell_count = notifier.format_email_body(results, None, mode="reminder")
        subject = f"[REVERSALS] REMINDER — {buy_count} BUY, {sell_count} SELL — {digest_id}"

        if args.dry_run:
            logger.info("Dry Run - Reminder Email Content:")
            logger.info(body)
        else:
            notifier.send_email(subject, body)

        state_manager.mark_reminder_sent(state, digest_id)
        state_manager.save(state)
        return

    if not td_api_key:
        logger.error("TWELVE_DATA_API_KEY not set")
        return

    fetcher = TwelveDataFetcher(td_api_key)
    calculator = TechnicalCalculator()
    reversal_calc = ReversalCalculator()
    trigger_engine = TriggerEngine(default_triggers)
    notifier = Notifier(resend_api_key, email_from, email_to)

    symbols = [t['symbol'] for t in tickers]
    logger.info(f"Starting scan for {len(symbols)} tickers...")

    # Fetch Data (with rate limiting)
    try:
        raw_data = fetcher.fetch_batch_time_series(symbols)
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        return

    results = []
    all_matrix_data = []  # Matrix for ALL tickers
    triggered_items_for_state = []
    trigger_keys_fired_today = []
    
    # Process each ticker
    for ticker_conf in tickers:
        symbol = ticker_conf['symbol']
        theme = ticker_conf.get('theme', 'Unknown')
        
        # Use ticker-specific triggers if defined, otherwise None (engine uses defaults)
        ticker_triggers = ticker_conf.get('triggers', None)
        
        data_ts = raw_data.get(symbol)
        if not data_ts:
            logger.warning(f"No data for {symbol}")
            continue
            
        # Calculate indicators and score
        df = calculator.process_data(data_ts)
        if df is None or df.empty:
            logger.warning(f"Could not process data for {symbol}")
            continue
            
        score, breakdown = calculator.calculate_bullish_score(df)
        price = df.iloc[-1]['close']
        
        # Calculate matrix (for ALL tickers)
        matrix = calculator.calculate_matrix(df)
        matrix['symbol'] = symbol
        matrix['theme'] = theme
        matrix['score'] = score

        # Add full indicator data for Supabase archiving
        curr = df.iloc[-1]
        matrix['close'] = float(curr['close'])
        matrix['rsi'] = float(curr.get('RSI')) if curr.get('RSI') is not None else None
        matrix['stoch_k'] = float(curr.get('STOCH_K')) if curr.get('STOCH_K') is not None else None
        matrix['stoch_d'] = float(curr.get('STOCH_D')) if curr.get('STOCH_D') is not None else None
        matrix['williams_r'] = float(curr.get('WILLIAMS_R')) if curr.get('WILLIAMS_R') is not None else None
        matrix['roc'] = float(curr.get('ROC')) if curr.get('ROC') is not None else None
        matrix['macd'] = float(curr.get('MACD')) if curr.get('MACD') is not None else None
        matrix['macd_signal'] = float(curr.get('MACD_SIGNAL')) if curr.get('MACD_SIGNAL') is not None else None
        matrix['macd_hist'] = float(curr.get('MACD_HIST')) if curr.get('MACD_HIST') is not None else None
        matrix['adx'] = float(curr.get('ADX')) if curr.get('ADX') is not None else None
        matrix['sma_20'] = float(curr.get('SMA_20')) if curr.get('SMA_20') is not None else None
        matrix['sma_50'] = float(curr.get('SMA_50')) if curr.get('SMA_50') is not None else None
        matrix['sma_200'] = float(curr.get('SMA_200')) if curr.get('SMA_200') is not None else None
        matrix['bb_upper'] = float(curr.get('BB_UPPER')) if curr.get('BB_UPPER') is not None else None
        matrix['bb_lower'] = float(curr.get('BB_LOWER')) if curr.get('BB_LOWER') is not None else None
        matrix['bb_position'] = float((curr['close'] - curr.get('BB_LOWER', 0)) / (curr.get('BB_UPPER', 1) - curr.get('BB_LOWER', 0))) if curr.get('BB_UPPER') and curr.get('BB_LOWER') and curr.get('BB_UPPER') != curr.get('BB_LOWER') else None
        matrix['atr'] = float(curr.get('ATR')) if curr.get('ATR') is not None else None
        matrix['volume'] = int(curr.get('volume')) if curr.get('volume') is not None else None
        matrix['obv'] = int(curr.get('OBV')) if curr.get('OBV') is not None else None

        all_matrix_data.append(matrix)
        
        # Calculate Reversal Analysis
        reversal_analysis = reversal_calc.get_full_reversal_analysis(df, symbol)
        upside_rev_score = reversal_analysis['upside_reversal_score']
        downside_rev_score = reversal_analysis['downside_reversal_score']
        upside_conviction = reversal_analysis.get('upside_conviction', 'NONE')
        downside_conviction = reversal_analysis.get('downside_conviction', 'NONE')
        reversal_triggers_raw = reversal_analysis['upside_triggers'] + reversal_analysis['downside_triggers']

        # Add reversal data to matrix (upside only - focus on BUY signals)
        matrix['upside_rev_score'] = upside_rev_score
        matrix['upside_conviction'] = upside_conviction
        matrix['reversal_signal'] = reversal_analysis['signal']

        # Add detailed reversal breakdown for Supabase archiving
        upside_breakdown = reversal_analysis.get('upside_breakdown', {})
        matrix['reversal_components'] = {
            k: v for k, v in upside_breakdown.items()
            if k not in ('volume_multiplier', 'volume_ratio', 'adx_multiplier',
                         'adx_value', 'divergence_type', 'raw_score', 'conviction')
        }
        matrix['reversal_conviction'] = upside_conviction
        matrix['raw_score'] = upside_breakdown.get('raw_score')
        matrix['volume_multiplier'] = upside_breakdown.get('volume_multiplier')
        matrix['adx_multiplier'] = upside_breakdown.get('adx_multiplier')
        # Parse divergence info (case-insensitive)
        div_type_desc = str(upside_breakdown.get('divergence_type', 'None')).lower()
        if 'bullish' in div_type_desc:
            matrix['divergence_type'] = 'bullish'
        elif 'bearish' in div_type_desc:
            matrix['divergence_type'] = 'bearish'
        else:
            matrix['divergence_type'] = 'none'
        # Divergence strength from components if available
        matrix['divergence_strength'] = upside_breakdown.get('divergence', 0)

        # Evaluate config-based Triggers
        triggers = trigger_engine.evaluate(symbol, df, score, ticker_triggers, matrix=matrix)

        # Convert reversal_triggers to standard trigger format and merge
        # IMPORTANT: Only include HIGH conviction signals for actionable alerts
        for rt in reversal_triggers_raw:
            trigger_id = rt.get('id', 'REV-UNKNOWN')
            trigger_name = rt.get('name', 'Reversal Signal')
            priority = rt.get('priority', 'MEDIUM')

            # Determine action based on trigger type
            if trigger_id.startswith('REV-UP'):
                action = 'BUY'
                signal_type = 'UPSIDE_REVERSAL'
                conviction = upside_conviction
            else:
                action = 'SELL'
                signal_type = 'DOWNSIDE_REVERSAL'
                conviction = downside_conviction

            # CRITICAL: Only include HIGH conviction signals in alerts
            # LOW and NONE are noise, MEDIUM is developing (could be watchlist in future)
            if conviction != 'HIGH':
                logger.debug(f"Skipping {symbol} {trigger_id} - conviction {conviction} (not HIGH)")
                continue

            triggers.append({
                'symbol': symbol,
                'action': action,
                'type': signal_type,
                'conviction': conviction,
                'message': f"{action}: {trigger_name} ({trigger_id}) [🔥HIGH]",
                'trigger_key': f"{symbol}_{trigger_id}",
                'cooldown_days': 7,  # Default cooldown for reversal signals
            })

        # Track triggers for state + compute "new" triggers only (no repeat spam)
        if triggers:
            # Apply archive suppression at the trigger level
            for t in triggers:
                k = t.get("trigger_key")
                t["suppressed"] = True if (k and archive_manager.is_suppressed(archive, k)) else False

                # Cooldown suppression: if we saw this trigger recently (even if it disappeared yesterday),
                # avoid re-alerting within the configured window.
                cooldown_days = int(t.get("cooldown_days", 0) or 0)
                if cooldown_days > 0 and k:
                    last_seen_raw = (state.get("seen_triggers") or {}).get(k, {}).get("last_seen")
                    try:
                        if last_seen_raw and isinstance(last_seen_raw, str):
                            iso = last_seen_raw[:-1] + "+00:00" if last_seen_raw.endswith("Z") else last_seen_raw
                            last_seen_dt = datetime.fromisoformat(iso)
                            if last_seen_dt.tzinfo is None:
                                last_seen_dt = last_seen_dt.replace(tzinfo=timezone.utc)
                            now_dt = datetime.now(timezone.utc)
                            if now_dt - last_seen_dt < timedelta(days=cooldown_days):
                                t["suppressed"] = True
                    except Exception:
                        pass

            trigger_keys = [t.get("trigger_key") for t in triggers if t.get("trigger_key")]
            trigger_messages = [t.get("message") for t in triggers if t.get("message")]
            trigger_keys_fired_today.extend(trigger_keys)

            for t in triggers:
                k = t.get("trigger_key")
                m = t.get("message")
                if k and m:
                    triggered_items_for_state.append({"symbol": symbol, "trigger_key": k, "message": m})

            new_trigger_dicts = [
                t for t in triggers
                if t.get("trigger_key")
                and t.get("trigger_key") not in last_run_trigger_keys
                and not t.get("suppressed", False)
            ]
            if new_trigger_dicts:
                new_messages = [t.get("message") for t in new_trigger_dicts if t.get("message")]
                new_keys = [t.get("trigger_key") for t in new_trigger_dicts if t.get("trigger_key")]
                results.append({
                    'symbol': symbol,
                    'theme': theme,
                    'score': score,
                    'price': round(price, 2),
                    'triggers': new_messages,
                    'trigger_keys': new_keys,
                })
                logger.info(f"NEW triggers for {symbol}: {new_messages}")
        else:
            logger.debug(f"No triggers for {symbol} (Score: {score})")

    # Update state regardless of whether we email
    state_manager.update_seen_triggers(state, triggered_items_for_state)
    state_manager.set_last_run(state, trigger_keys_fired_today)

    # Archive to Supabase (non-blocking)
    try:
        archived = archive_daily_indicators(all_matrix_data, score_type="reversal")
        if archived > 0:
            logger.info(f"Archived {archived} indicators to Supabase")
    except Exception as e:
        logger.warning(f"Failed to archive to Supabase: {e}")

    # Build top 20 by upside reversal score (daily leaderboard)
    top_20_by_score = sorted(
        [m for m in all_matrix_data if (m.get('upside_rev_score') or 0) > 0],
        key=lambda x: x.get('upside_rev_score', 0) or 0,
        reverse=True
    )[:20]

    top_5_preview = [f"{m.get('symbol')}:{m.get('upside_rev_score', 0):.1f}" for m in top_20_by_score[:5]]
    logger.info(f"Top 20 by reversal score: {top_5_preview}...")

    # Notify: always send if we have top 20 data, even without HIGH conviction triggers
    has_high_conviction = bool(results)
    has_top_20 = bool(top_20_by_score)

    if has_high_conviction or has_top_20:
        body, buy_count, sell_count = notifier.format_email_body(
            results, all_matrix_data, top_20=top_20_by_score
        )

        # Build subject line
        if has_high_conviction:
            subject = f"[REVERSALS] {buy_count} BUY, {sell_count} SELL — {datetime.now().strftime('%b %d')}"
        else:
            subject = f"[REVERSALS] Top 20 Scores — {datetime.now().strftime('%b %d')}"

        if args.dry_run:
            logger.info("Dry Run - Email Content:")
            logger.info(body)
        else:
            notifier.send_email(subject, body)

        # Persist what we actually emailed at the main run (used for reminders later)
        digest = Digest(
            digest_id=datetime.utcnow().strftime("%Y-%m-%d"),
            sent_at=datetime.utcnow().isoformat() + "Z",
            results=results,
            buy_count=buy_count,
            sell_count=sell_count,
        )
        state_manager.set_last_digest(state, digest)
    else:
        if args.dry_run:
            logger.info("Dry Run - No data to email (no triggers and no scored tickers).")
        else:
            logger.info("No data to email. Skipping.")

    state_manager.save(state)


if __name__ == "__main__":
    main()
