"""
Supabase client for archiving daily indicator snapshots.

Archives computed technical indicators to Supabase for historical analysis,
backtesting, and pattern recognition.
"""

import logging
import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class IndicatorSnapshot:
    """A single day's indicator values for one ticker."""
    date: str
    symbol: str
    close: float
    # Momentum
    rsi: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    williams_r: Optional[float] = None
    roc: Optional[float] = None
    # Trend
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    adx: Optional[float] = None
    # Moving averages
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    # Volatility
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_position: Optional[float] = None
    atr: Optional[float] = None
    # Volume
    volume: Optional[int] = None
    volume_ratio: Optional[float] = None
    obv: Optional[int] = None
    # Scores
    bullish_score: Optional[float] = None
    reversal_score: Optional[float] = None
    oversold_score: Optional[float] = None
    action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase insert."""
        return {
            "date": self.date,
            "symbol": self.symbol,
            "close": self.close,
            "rsi": self.rsi,
            "stoch_k": self.stoch_k,
            "stoch_d": self.stoch_d,
            "williams_r": self.williams_r,
            "roc": self.roc,
            "macd": self.macd,
            "macd_signal": self.macd_signal,
            "macd_hist": self.macd_hist,
            "adx": self.adx,
            "sma_20": self.sma_20,
            "sma_50": self.sma_50,
            "sma_200": self.sma_200,
            "bb_upper": self.bb_upper,
            "bb_lower": self.bb_lower,
            "bb_position": self.bb_position,
            "atr": self.atr,
            "volume": self.volume,
            "volume_ratio": self.volume_ratio,
            "obv": self.obv,
            "bullish_score": self.bullish_score,
            "reversal_score": self.reversal_score,
            "oversold_score": self.oversold_score,
            "action": self.action,
        }


class SupabaseArchiver:
    """
    Archives daily indicator snapshots to Supabase.

    Uses the service_role key to bypass RLS for server-side operations.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
    ):
        """
        Initialize the Supabase archiver.

        Args:
            url: Supabase project URL (defaults to SUPABASE_URL env var)
            key: Supabase service role key (defaults to SUPABASE_SERVICE_KEY env var)
        """
        self.url = url or os.environ.get("SUPABASE_URL")
        self.key = key or os.environ.get("SUPABASE_SERVICE_KEY")
        self._client = None

        if not self.url or not self.key:
            logger.warning(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
            )

    @property
    def client(self):
        """Lazy-load the Supabase client."""
        if self._client is None:
            if not self.url or not self.key:
                raise ValueError(
                    "Supabase credentials not configured. "
                    "Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
                )
            try:
                from supabase import create_client
                self._client = create_client(self.url, self.key)
            except ImportError:
                raise ImportError(
                    "supabase package not installed. Run: pip install supabase"
                )
        return self._client

    @property
    def is_configured(self) -> bool:
        """Check if Supabase credentials are available."""
        return bool(self.url and self.key)

    def archive_snapshots(
        self,
        snapshots: List[IndicatorSnapshot],
    ) -> int:
        """
        Archive indicator snapshots to Supabase.

        Uses upsert to handle re-runs on the same day.

        Args:
            snapshots: List of IndicatorSnapshot objects to archive

        Returns:
            Number of records upserted
        """
        if not snapshots:
            logger.info("No snapshots to archive")
            return 0

        if not self.is_configured:
            logger.warning("Supabase not configured, skipping archive")
            return 0

        records = [s.to_dict() for s in snapshots]

        try:
            # Upsert in batches of 500 to avoid payload limits
            batch_size = 500
            total_upserted = 0

            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                self.client.table("daily_indicators").upsert(
                    batch, on_conflict="date,symbol"
                ).execute()
                total_upserted += len(batch)
                logger.debug(f"Upserted batch {i // batch_size + 1}: {len(batch)} records")

            logger.info(f"Archived {total_upserted} indicator snapshots to Supabase")
            return total_upserted

        except Exception as e:
            logger.error(f"Failed to archive to Supabase: {e}")
            raise

    def get_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 365,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical indicator data for a symbol.

        Args:
            symbol: Ticker symbol
            start_date: Start date (YYYY-MM-DD), optional
            end_date: End date (YYYY-MM-DD), optional
            limit: Maximum records to return (default 365)

        Returns:
            List of indicator records
        """
        if not self.is_configured:
            logger.warning("Supabase not configured")
            return []

        try:
            query = (
                self.client
                .table("daily_indicators")
                .select("*")
                .eq("symbol", symbol)
                .order("date", desc=True)
                .limit(limit)
            )

            if start_date:
                query = query.gte("date", start_date)
            if end_date:
                query = query.lte("date", end_date)

            result = query.execute()
            return result.data

        except Exception as e:
            logger.error(f"Failed to fetch history from Supabase: {e}")
            return []

    def get_latest_scores(
        self,
        score_type: str = "bullish_score",
        min_score: float = 7.0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get tickers with highest scores from the latest day.

        Args:
            score_type: Which score to filter by (bullish_score, reversal_score, oversold_score)
            min_score: Minimum score threshold
            limit: Maximum records to return

        Returns:
            List of ticker records with high scores
        """
        if not self.is_configured:
            return []

        try:
            # Get the latest date in the database
            latest = (
                self.client
                .table("daily_indicators")
                .select("date")
                .order("date", desc=True)
                .limit(1)
                .execute()
            )

            if not latest.data:
                return []

            latest_date = latest.data[0]["date"]

            # Get high-scoring tickers from that date
            result = (
                self.client
                .table("daily_indicators")
                .select("*")
                .eq("date", latest_date)
                .gte(score_type, min_score)
                .order(score_type, desc=True)
                .limit(limit)
                .execute()
            )

            return result.data

        except Exception as e:
            logger.error(f"Failed to fetch latest scores: {e}")
            return []


# Module-level convenience functions

_archiver: Optional[SupabaseArchiver] = None


def _get_archiver() -> SupabaseArchiver:
    """Get or create the singleton archiver instance."""
    global _archiver
    if _archiver is None:
        _archiver = SupabaseArchiver()
    return _archiver


def archive_daily_indicators(
    results,
    scan_date: Optional[date] = None,
    score_type: str = "bullish",
) -> int:
    """
    Archive indicator data to Supabase.

    Accepts either:
    - List of TickerResult objects (from 009-reversals, 010-oversold)
    - Dict of {symbol: flags_dict} (from 008-alerts)

    Args:
        results: List of TickerResult objects OR dict of {symbol: flags}
        scan_date: Date of the scan (defaults to today)
        score_type: Type of score in results ("bullish", "reversal", "oversold")

    Returns:
        Number of records archived
    """
    if not results:
        return 0

    archiver = _get_archiver()
    if not archiver.is_configured:
        logger.debug("Supabase not configured, skipping archive")
        return 0

    date_str = (scan_date or date.today()).isoformat()

    snapshots = []

    # Handle dict format from 008-alerts: {symbol: flags_dict}
    if isinstance(results, dict):
        for symbol, flags in results.items():
            if not isinstance(flags, dict):
                continue

            # Determine score type
            score_value = flags.get('score')
            bullish_score = score_value if score_type == "bullish" else None
            reversal_score = score_value if score_type == "reversal" else None
            oversold_score = score_value if score_type == "oversold" else None

            snapshot = IndicatorSnapshot(
                date=date_str,
                symbol=symbol,
                close=flags.get('close', 0.0),
                rsi=flags.get('rsi'),
                sma_50=flags.get('sma50'),
                sma_200=flags.get('sma200'),
                bullish_score=bullish_score,
                reversal_score=reversal_score,
                oversold_score=oversold_score,
            )
            snapshots.append(snapshot)
    else:
        # Handle list format from 009-reversals (list of dicts) or 010-oversold (list of objects)
        for r in results:
            # Check if it's a dict (matrix data) or an object (TickerResult)
            if isinstance(r, dict):
                # Dict data from all scanners: {symbol, close, rsi, stoch_k, macd, ...}
                symbol = r.get('symbol', '')
                # Support both _price (legacy) and close (standard)
                close = r.get('close') or r.get('_price', 0.0)
                # Support both _rsi (legacy) and rsi (standard)
                rsi = r.get('rsi') or r.get('_rsi')

                # Determine score fields based on score_type
                score_value = r.get('score')
                upside_rev = r.get('upside_rev_score')
                bullish_score = r.get('bullish_score') or (score_value if score_type == "bullish" else None)
                reversal_score = upside_rev if score_type == "reversal" else None
                oversold_score = r.get('oversold_score') or (score_value if score_type == "oversold" else None)

                snapshot = IndicatorSnapshot(
                    date=date_str,
                    symbol=symbol,
                    close=close,
                    # Momentum
                    rsi=rsi,
                    stoch_k=r.get('stoch_k'),
                    stoch_d=r.get('stoch_d'),
                    williams_r=r.get('williams_r'),
                    roc=r.get('roc'),
                    # Trend
                    macd=r.get('macd'),
                    macd_signal=r.get('macd_signal'),
                    macd_hist=r.get('macd_hist'),
                    adx=r.get('adx'),
                    # Moving averages
                    sma_20=r.get('sma_20'),
                    sma_50=r.get('sma_50'),
                    sma_200=r.get('sma_200'),
                    # Volatility
                    bb_upper=r.get('bb_upper'),
                    bb_lower=r.get('bb_lower'),
                    bb_position=r.get('bb_position'),
                    atr=r.get('atr'),
                    # Volume
                    volume=r.get('volume'),
                    volume_ratio=r.get('volume_ratio'),
                    obv=r.get('obv'),
                    # Scores
                    bullish_score=bullish_score,
                    reversal_score=reversal_score,
                    oversold_score=oversold_score,
                )
                snapshots.append(snapshot)
            else:
                # Object format (TickerResult) from 010-oversold or other projects
                # Handle both 'symbol' and 'ticker' attribute names
                symbol = getattr(r, 'symbol', None) or getattr(r, 'ticker', '')
                # Handle both 'close' and 'price' attribute names
                close = getattr(r, 'close', None) or getattr(r, 'price', 0.0)

                # Try to get indicator values from object attributes first,
                # then from flags/metadata dicts
                flags = getattr(r, 'flags', {}) or {}
                metadata = getattr(r, 'metadata', {}) or {}
                components = getattr(r, 'components', {}) or {}

                # Determine which score field to populate
                score_value = getattr(r, 'score', None)
                bullish_score = score_value if score_type == "bullish" else None
                reversal_score = score_value if score_type == "reversal" else None
                oversold_score = score_value if score_type == "oversold" else None

                # Get indicator values - check object attributes first, then dicts
                rsi = getattr(r, 'rsi', None) or flags.get('rsi') or metadata.get('rsi')
                stoch_k = getattr(r, 'stoch_k', None) or flags.get('stoch_k') or metadata.get('stoch_k')
                stoch_d = getattr(r, 'stoch_d', None) or flags.get('stoch_d') or metadata.get('stoch_d')
                williams_r = getattr(r, 'williams_r', None) or flags.get('williams_r') or metadata.get('williams_r')

                snapshot = IndicatorSnapshot(
                    date=date_str,
                    symbol=symbol,
                    close=close,
                    # Momentum
                    rsi=rsi,
                    stoch_k=stoch_k,
                    stoch_d=stoch_d,
                    williams_r=williams_r,
                    roc=flags.get('roc') or metadata.get('roc'),
                    # Trend
                    macd=flags.get('macd') or metadata.get('macd'),
                    macd_signal=flags.get('macd_signal') or metadata.get('macd_signal'),
                    macd_hist=flags.get('macd_hist') or metadata.get('macd_hist'),
                    adx=flags.get('adx') or metadata.get('adx'),
                    # Moving averages
                    sma_20=flags.get('sma_20') or metadata.get('sma_20'),
                    sma_50=flags.get('sma_50') or metadata.get('sma_50'),
                    sma_200=flags.get('sma_200') or metadata.get('sma_200'),
                    # Volatility
                    bb_upper=flags.get('bb_upper') or metadata.get('bb_upper'),
                    bb_lower=flags.get('bb_lower') or metadata.get('bb_lower'),
                    bb_position=flags.get('bb_position') or metadata.get('bb_position') or components.get('bb_position'),
                    atr=flags.get('atr') or metadata.get('atr'),
                    # Volume
                    volume=flags.get('volume') or metadata.get('volume'),
                    volume_ratio=flags.get('volume_ratio') or metadata.get('volume_ratio'),
                    obv=flags.get('obv') or metadata.get('obv'),
                    # Scores
                    bullish_score=bullish_score,
                    reversal_score=reversal_score,
                    oversold_score=oversold_score,
                    action=getattr(r, 'action', None),
                )
                snapshots.append(snapshot)

    return archiver.archive_snapshots(snapshots)


def get_historical_data(
    symbol: str,
    days: int = 90,
) -> List[Dict[str, Any]]:
    """
    Get historical indicator data for a symbol.

    Args:
        symbol: Ticker symbol
        days: Number of days of history to retrieve

    Returns:
        List of historical indicator records
    """
    archiver = _get_archiver()
    return archiver.get_history(symbol, limit=days)
