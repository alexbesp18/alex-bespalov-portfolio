#!/usr/bin/env python3
"""Oversold Screener — Top N Most Oversold Stocks.

A local CLI tool that ranks stocks by oversold score across flexible watchlists.

Usage:
    python oversold.py --watchlist ai              # Single watchlist
    python oversold.py --watchlist ai,portfolio    # Multiple watchlists
    python oversold.py --all                       # All watchlists
    python oversold.py --all --top 5               # Top 5 only
    python oversold.py --all --output json         # JSON output

Copyright 2024 Alex Bespalov. MIT License.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from src import (
    OversoldScorer,
    TechnicalCalculator,
    TwelveDataFetcher,
    TickerResult,
    Watchlist,
    OutputFormat,
)
from shared_core import archive_daily_indicators


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure and return the logger.
    
    Args:
        verbose: If True, set level to DEBUG; otherwise INFO.
        
    Returns:
        Configured logger instance.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("OVERSOLD")


# =============================================================================
# OUTPUT FORMATTERS
# =============================================================================

class OutputFormatter:
    """Handles formatting of scan results for various output types."""
    
    @staticmethod
    def print_header(title: str, width: int = 72) -> None:
        """Print a styled header."""
        print()
        print("═" * width)
        print(f"{title:^{width}}")
        print("═" * width)
    
    @staticmethod
    def print_table(results: List[TickerResult], top_n: int) -> None:
        """Print results as a formatted ASCII table.
        
        Args:
            results: Sorted list of TickerResult objects.
            top_n: Number shown (for header title).
        """
        OutputFormatter.print_header(f"TOP {top_n} MOST OVERSOLD")
        
        # Header row
        header = f"{'Rank':^6}│{'Ticker':^8}│{'Score':^8}│{'RSI':^7}│{'Will%R':^8}│{'Stoch':^7}│{'Price':^10}"
        print(header)
        print("━" * 72)
        
        # Data rows
        for rank, result in enumerate(results, 1):
            row = (
                f"{rank:^6}│"
                f"{result.ticker:^8}│"
                f"{result.score:^8.1f}│"
                f"{result.rsi:^7.1f}│"
                f"{result.williams_r:^8.1f}│"
                f"{result.stoch_k:^7.1f}│"
                f"${result.price:>8.2f}"
            )
            print(row)
        
        # Footer
        print("═" * 72)
        print()
    
    @staticmethod
    def print_json(results: List[TickerResult]) -> None:
        """Print results as JSON."""
        output = [r.to_dict() for r in results]
        print(json.dumps(output, indent=2))
    
    @staticmethod
    def print_csv(results: List[TickerResult]) -> None:
        """Print results as CSV."""
        print("rank,ticker,score,rsi,williams_r,stoch_k,price")
        for rank, r in enumerate(results, 1):
            print(f"{rank},{r.ticker},{r.score},{r.rsi},{r.williams_r},{r.stoch_k},{r.price}")
    
    @staticmethod
    def print_verbose(results: List[TickerResult]) -> None:
        """Print detailed component breakdown."""
        print("\nComponent Breakdown:")
        for result in results:
            print(f"\n{result.ticker}:")
            for key, value in result.components.items():
                print(f"  {key}: {value:.1f}")


# =============================================================================
# WATCHLIST MANAGEMENT
# =============================================================================

def get_cached_tickers(cache_dir: Path) -> List[str]:
    """
    Get tickers from 007-ticker-analysis cache.
    Tries today first, then falls back to most recent date available.
    """
    from datetime import datetime
    import re

    if not cache_dir.exists():
        return []

    # Try today's files first
    today = datetime.now().strftime('%Y-%m-%d')
    tickers = []
    for f in cache_dir.glob(f"*_{today}.json"):
        ticker = f.stem.replace(f"_{today}", "")
        if ticker:
            tickers.append(ticker)

    if tickers:
        return sorted(set(tickers))

    # Fallback: find most recent date in cache
    date_pattern = re.compile(r'_(\d{4}-\d{2}-\d{2})\.json$')
    dates = set()
    for f in cache_dir.glob("*_????-??-??.json"):
        match = date_pattern.search(f.name)
        if match:
            dates.add(match.group(1))

    if not dates:
        return []

    # Use most recent date
    latest_date = max(dates)
    for f in cache_dir.glob(f"*_{latest_date}.json"):
        ticker = f.stem.replace(f"_{latest_date}", "")
        if ticker:
            tickers.append(ticker)

    return sorted(set(tickers))


class WatchlistManager:
    """Manages loading and combining watchlists from JSON files."""
    
    def __init__(self, watchlist_dir: Path, cache_dir: Optional[Path] = None) -> None:
        """Initialize with the watchlist directory path.
        
        Args:
            watchlist_dir: Path to directory containing watchlist JSON files.
            cache_dir: Optional path to 007-ticker-analysis cache for fallback.
        """
        self.watchlist_dir = watchlist_dir
        self.cache_dir = cache_dir
    
    def list_available(self) -> List[str]:
        """List all available watchlist names (without .json extension).
        
        Returns:
            List of watchlist names.
        """
        if not self.watchlist_dir.exists():
            return []
        return [f.stem for f in self.watchlist_dir.glob("*.json")]
    
    def get_cached_tickers(self) -> List[str]:
        """Get tickers from cache as fallback."""
        if self.cache_dir:
            return get_cached_tickers(self.cache_dir)
        return []
    
    def load(self, name: str) -> Watchlist:
        """Load a single watchlist by name.
        
        Args:
            name: Watchlist name (without .json extension).
            
        Returns:
            Watchlist object with name and tickers.
        """
        path = self.watchlist_dir / f"{name}.json"
        if not path.exists():
            return Watchlist(name=name, tickers=[])
        
        with open(path, "r") as f:
            data = json.load(f)
        
        return Watchlist(
            name=data.get("name", name),
            tickers=data.get("tickers", []),
        )
    
    def load_multiple(self, names: List[str]) -> Dict[str, List[str]]:
        """Load multiple watchlists and return combined tickers.
        
        Args:
            names: List of watchlist names to load.
            
        Returns:
            Dict with 'all_tickers' (unique) and 'by_watchlist' mapping.
        """
        all_tickers: set = set()
        by_watchlist: Dict[str, List[str]] = {}
        
        for name in names:
            watchlist = self.load(name)
            by_watchlist[name] = watchlist.tickers
            all_tickers.update(watchlist.tickers)
        
        return {
            "all_tickers": list(all_tickers),
            "by_watchlist": by_watchlist,
        }


# =============================================================================
# MAIN SCANNER
# =============================================================================

class OversoldScanner:
    """Main scanner that orchestrates data fetching, analysis, and output."""
    
    def __init__(
        self,
        api_key: str,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize the scanner with API credentials.
        
        Args:
            api_key: TwelveData API key.
            logger: Optional logger instance.
        """
        self.fetcher = TwelveDataFetcher(api_key)
        self.calculator = TechnicalCalculator()
        self.scorer = OversoldScorer()
        self.logger = logger or logging.getLogger(__name__)
    
    def scan(self, tickers: List[str]) -> List[TickerResult]:
        """Scan a list of tickers and return ranked results.
        
        Args:
            tickers: List of stock symbols to scan.
            
        Returns:
            List of TickerResult sorted by score (descending).
        """
        self.logger.info(f"Scanning {len(tickers)} unique tickers...")
        
        # Fetch data
        try:
            raw_data = self.fetcher.fetch_batch_time_series(tickers)
        except Exception as e:
            self.logger.error(f"Failed to fetch data: {e}")
            return []
        
        # Process each ticker
        results: List[TickerResult] = []
        archive_data = []  # Full indicator data for Supabase

        for ticker in tickers:
            data_ts = raw_data.get(ticker)
            if not data_ts:
                self.logger.warning(f"No data for {ticker}")
                continue
            
            # Calculate technical indicators
            df = self.calculator.process_data(data_ts)
            if df is None or df.empty:
                self.logger.warning(f"Could not process data for {ticker}")
                continue
            
            # Calculate oversold score
            score_result = self.scorer.score(df)
            
            # Merge components with raw_values for email display (pct_from_high, etc.)
            merged_components = {**score_result.components, **score_result.raw_values}
            
            results.append(TickerResult(
                ticker=ticker,
                score=score_result.final_score,
                rsi=score_result.raw_values.get("rsi", 0),
                williams_r=score_result.raw_values.get("williams_r", 0),
                stoch_k=score_result.raw_values.get("stoch_k", 0),
                price=score_result.raw_values.get("close", 0),
                components=merged_components,
            ))

            # Collect full indicator data for Supabase archiving
            curr = df.iloc[-1]
            archive_data.append({
                'symbol': ticker,
                'close': float(curr['close']),
                'rsi': float(curr.get('RSI')) if curr.get('RSI') is not None else None,
                'stoch_k': float(curr.get('STOCH_K')) if curr.get('STOCH_K') is not None else None,
                'stoch_d': float(curr.get('STOCH_D')) if curr.get('STOCH_D') is not None else None,
                'williams_r': float(curr.get('WILLIAMS_R')) if curr.get('WILLIAMS_R') is not None else None,
                'roc': float(curr.get('ROC')) if curr.get('ROC') is not None else None,
                'macd': float(curr.get('MACD')) if curr.get('MACD') is not None else None,
                'macd_signal': float(curr.get('MACD_SIGNAL')) if curr.get('MACD_SIGNAL') is not None else None,
                'macd_hist': float(curr.get('MACD_HIST')) if curr.get('MACD_HIST') is not None else None,
                'adx': float(curr.get('ADX')) if curr.get('ADX') is not None else None,
                'sma_20': float(curr.get('SMA_20')) if curr.get('SMA_20') is not None else None,
                'sma_50': float(curr.get('SMA_50')) if curr.get('SMA_50') is not None else None,
                'sma_200': float(curr.get('SMA_200')) if curr.get('SMA_200') is not None else None,
                'bb_upper': float(curr.get('BB_UPPER')) if curr.get('BB_UPPER') is not None else None,
                'bb_lower': float(curr.get('BB_LOWER')) if curr.get('BB_LOWER') is not None else None,
                'bb_position': float((curr['close'] - curr.get('BB_LOWER', 0)) / (curr.get('BB_UPPER', 1) - curr.get('BB_LOWER', 0))) if curr.get('BB_UPPER') and curr.get('BB_LOWER') and curr.get('BB_UPPER') != curr.get('BB_LOWER') else None,
                'atr': float(curr.get('ATR')) if curr.get('ATR') is not None else None,
                'volume': int(curr.get('volume')) if curr.get('volume') is not None else None,
                'obv': int(curr.get('OBV')) if curr.get('OBV') is not None else None,
                'oversold_score': score_result.final_score,
            })
        
        # Sort by score (descending — higher = more oversold)
        results.sort(key=lambda x: x.score, reverse=True)

        self.logger.info(f"Scan complete. Processed {len(results)} tickers.")

        # Archive to Supabase (non-blocking)
        try:
            archived = archive_daily_indicators(archive_data, score_type="oversold")
            if archived > 0:
                self.logger.info(f"Archived {archived} indicators to Supabase")
        except Exception as e:
            self.logger.warning(f"Failed to archive to Supabase: {e}")

        return results


# =============================================================================
# CLI ARGUMENT PARSING
# =============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Top N Most Oversold Stock Screener",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python oversold.py --watchlist ai
  python oversold.py --watchlist ai,portfolio
  python oversold.py --all --top 10
  python oversold.py --all --output json
        """,
    )
    
    # Watchlist selection (mutually exclusive behavior)
    parser.add_argument(
        "--watchlist", "-w",
        type=str,
        default=None,
        help="Watchlist name(s), comma-separated",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all available watchlists",
    )
    
    # Output options
    parser.add_argument(
        "--top", "-n",
        type=int,
        default=10,
        help="Number of top oversold stocks to show (default: 10)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed breakdown for each stock",
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="Send results via email (requires RESEND_API_KEY)",
    )
    
    return parser.parse_args()


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for error).
    """
    load_dotenv()
    args = parse_args()
    logger = setup_logging(args.verbose)
    
    # Validate inputs
    if not args.watchlist and not args.all:
        logger.error("Please specify --watchlist or --all")
        return 1
    
    # Setup paths
    base_dir = Path(__file__).parent.resolve()
    watchlist_dir = base_dir / "config" / "watchlists"
    cache_dir = base_dir.parent / "007-ticker-analysis" / "data" / "twelve_data"
    
    # Load watchlists
    manager = WatchlistManager(watchlist_dir, cache_dir)
    
    if args.all:
        watchlist_names = manager.list_available()
        if not watchlist_names:
            # Fallback: use cached tickers from 007-ticker-analysis
            tickers = manager.get_cached_tickers()
            if tickers:
                logger.info(f"Using cached tickers from 007-ticker-analysis: {len(tickers)} tickers")
            else:
                logger.error(f"No watchlists found in {watchlist_dir} and no cached data")
                return 1
        else:
            logger.info(f"Loading watchlists: {watchlist_names}")
            combined = manager.load_multiple(watchlist_names)
            tickers = combined["all_tickers"]
    else:
        watchlist_names = [n.strip() for n in args.watchlist.split(",")]
        logger.info(f"Loading watchlists: {watchlist_names}")
        combined = manager.load_multiple(watchlist_names)
        tickers = combined["all_tickers"]
    
    if not tickers:
        # Final fallback: try cache
        tickers = manager.get_cached_tickers()
        if tickers:
            logger.info(f"Watchlists empty, using cached tickers: {len(tickers)} tickers")
        else:
            logger.error("No tickers found in selected watchlists or cache")
            return 1
    
    # Check API key
    api_key = os.environ.get("TWELVE_DATA_API_KEY")
    if not api_key:
        logger.error("TWELVE_DATA_API_KEY not set. Check your .env file.")
        return 1
    
    # Run scan
    scanner = OversoldScanner(api_key, logger)
    results = scanner.scan(tickers)
    
    # Limit to top N
    top_results = results[:args.top]
    
    # Output
    output_format = OutputFormat(args.output)
    
    if output_format == OutputFormat.TABLE:
        OutputFormatter.print_table(top_results, args.top)
        if args.verbose:
            OutputFormatter.print_verbose(top_results)
    elif output_format == OutputFormat.JSON:
        OutputFormatter.print_json(top_results)
    elif output_format == OutputFormat.CSV:
        OutputFormatter.print_csv(top_results)
    
    # Send email if requested
    if args.email:
        resend_key = os.environ.get("RESEND_API_KEY")
        if not resend_key:
            logger.warning("RESEND_API_KEY not set. Skipping email.")
        else:
            try:
                from src.notifier import Notifier
                notifier = Notifier(resend_key)
                
                # Convert TickerResult to dict for notifier
                email_data = [
                    {
                        "symbol": r.ticker,
                        "oversold_score": r.score,
                        "price": r.price,
                        "rsi": r.rsi,
                        "williams_r": r.williams_r,
                        "pct_off_high": r.components.get("pct_from_high", 0),
                        "pct_below_sma200": r.components.get("sma200_distance", 0),
                    }
                    for r in top_results
                ]
                
                body, count = notifier.format_email_body(email_data)
                top_symbols = [r.ticker for r in top_results[:3]]
                subject = notifier.format_subject(count, top_symbols)
                
                if notifier.send_email(subject, body):
                    logger.info(f"Email sent successfully with {count} candidates")
                else:
                    logger.warning("Failed to send email")
            except Exception as e:
                logger.error(f"Email error: {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
