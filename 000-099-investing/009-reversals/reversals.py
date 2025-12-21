import os
import json
import logging
import argparse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from src.fetcher import TwelveDataFetcher
from src.calculator import TechnicalCalculator
from src.reversal_calculator import ReversalCalculator
from src.triggers import TriggerEngine
from src.notifier import Notifier
from src.state_manager import StateManager, Digest
from src.archiver import ArchiveManager

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("REVERSALS")


def load_watchlist(path):
    """Load watchlist from JSON file."""
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}


def get_cached_tickers(cache_dir):
    """
    Get tickers from 007-ticker-analysis cache (today's files).
    Default source when no custom JSON config is provided.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    tickers = []
    
    if os.path.exists(cache_dir):
        for f in os.listdir(cache_dir):
            if f.endswith(f"_{today}.json"):
                # Extract ticker from filename like "NVDA_2024-12-21.json"
                ticker = f.replace(f"_{today}.json", "")
                if ticker:
                    tickers.append(ticker)
    
    return sorted(set(tickers))


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

    # Optional time guard (useful when cron runs multiple times to handle DST)
    if args.expected_local_hour is not None:
        try:
            local_now = datetime.now(ZoneInfo(args.expected_tz))
            if local_now.hour != args.expected_local_hour:
                logger.info(
                    f"Time guard: local hour is {local_now.hour} in {args.expected_tz}; "
                    f"expected {args.expected_local_hour}. Skipping."
                )
                return
        except Exception as e:
            logger.warning(f"Time guard failed (tz={args.expected_tz}): {e}. Continuing without guard.")

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
        cached_symbols = get_cached_tickers(cache_dir)
        # Convert to format expected by the rest of the code
        tickers = [{'symbol': s, 'theme': 'Cached'} for s in cached_symbols]
        logger.info(f"Using cached tickers from 007-ticker-analysis: {len(tickers)} tickers")

    # Initialize Components
    td_api_key = os.environ.get("TWELVE_DATA_API_KEY")
    sg_api_key = os.environ.get("SENDGRID_API_KEY")
    email_to = os.environ.get("NOTIFICATION_EMAIL")
    email_from = os.environ.get("SENDER_EMAIL", email_to)

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
        notifier = Notifier(sg_api_key, email_from, email_to)
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
    notifier = Notifier(sg_api_key, email_from, email_to)

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
        all_matrix_data.append(matrix)
        
        # Calculate Reversal Analysis
        reversal_analysis = reversal_calc.get_full_reversal_analysis(df, symbol)
        upside_rev_score = reversal_analysis['upside_reversal_score']
        downside_rev_score = reversal_analysis['downside_reversal_score']
        reversal_triggers = reversal_analysis['upside_triggers'] + reversal_analysis['downside_triggers']
        
        # Add reversal data to matrix
        matrix['upside_rev_score'] = upside_rev_score
        matrix['downside_rev_score'] = downside_rev_score
        matrix['reversal_signal'] = reversal_analysis['signal']
        
        # Evaluate Triggers (original + reversal)
        triggers = trigger_engine.evaluate(symbol, df, score, ticker_triggers, matrix=matrix)

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

    # Notify (only on NEW triggers to prevent alert fatigue)
    if results:
        body, buy_count, sell_count = notifier.format_email_body(results, all_matrix_data)
        subject = f"[REVERSALS] {buy_count} BUY, {sell_count} SELL — {datetime.now().strftime('%b %d')}"
        
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
            logger.info("Dry Run - No NEW triggers found today. (No email would be sent.)")
        else:
            logger.info("No NEW triggers found today. Skipping email.")

    state_manager.save(state)


if __name__ == "__main__":
    main()
