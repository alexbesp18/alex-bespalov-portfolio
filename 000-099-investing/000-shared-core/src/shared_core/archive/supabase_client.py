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
            logger.debug(
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
            logger.debug("No snapshots to archive")
            return 0

        if not self.is_configured:
            logger.debug("Supabase not configured, skipping archive")
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
            logger.debug("Supabase not configured")
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
    results: List[Dict[str, Any]],
    scan_date: Optional[date] = None,
    score_type: str = "bullish",
) -> int:
    """
    Archive indicator data to Supabase.

    All scanners (008-alerts, 009-reversals, 010-oversold) pass a list of dicts
    with standardized field names. Each dict should contain:

    Required:
        - symbol: Ticker symbol (str)
        - close: Closing price (float)

    Optional indicators (pass whatever the scanner computes):
        - rsi, stoch_k, stoch_d, williams_r, roc
        - macd, macd_signal, macd_hist, adx
        - sma_20, sma_50, sma_200
        - bb_upper, bb_lower, bb_position, atr
        - volume, volume_ratio, obv

    Optional scores (one per scanner type):
        - bullish_score (008-alerts)
        - reversal_score or upside_rev_score (009-reversals)
        - oversold_score (010-oversold)

    Args:
        results: List of dicts with indicator data
        scan_date: Date of the scan (defaults to today)
        score_type: Type of scanner ("bullish", "reversal", "oversold")

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

    for r in results:
        if not isinstance(r, dict):
            logger.warning(f"Skipping non-dict result: {type(r)}")
            continue

        symbol = r.get('symbol', '')
        if not symbol:
            continue

        # Get close price (support legacy _price key)
        close = r.get('close') or r.get('_price', 0.0)

        # Get RSI (support legacy _rsi key)
        rsi = r.get('rsi') or r.get('_rsi')

        # Determine score based on score_type
        # Each scanner passes its own score field
        bullish_score = None
        reversal_score = None
        oversold_score = None

        if score_type == "bullish":
            bullish_score = r.get('bullish_score') or r.get('score')
        elif score_type == "reversal":
            # 009-reversals passes upside_rev_score for reversal score
            reversal_score = r.get('upside_rev_score') or r.get('reversal_score')
        elif score_type == "oversold":
            oversold_score = r.get('oversold_score') or r.get('score')

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
