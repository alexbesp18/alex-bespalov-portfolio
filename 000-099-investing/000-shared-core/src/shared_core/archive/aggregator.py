"""
Monthly aggregation for daily indicators.

Compresses daily data older than 90 days into monthly summaries,
preserving key statistics while reducing storage footprint by ~30x.
"""

import logging
import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MonthlyAggregate:
    """Monthly summary statistics for one ticker."""
    month: str  # YYYY-MM format
    symbol: str
    # Price stats
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    avg_price: float
    # Indicator averages
    avg_rsi: Optional[float] = None
    min_rsi: Optional[float] = None
    max_rsi: Optional[float] = None
    avg_stoch_k: Optional[float] = None
    avg_williams_r: Optional[float] = None
    avg_macd: Optional[float] = None
    avg_adx: Optional[float] = None
    # Score stats
    avg_bullish_score: Optional[float] = None
    max_bullish_score: Optional[float] = None
    avg_reversal_score: Optional[float] = None
    max_reversal_score: Optional[float] = None
    avg_oversold_score: Optional[float] = None
    max_oversold_score: Optional[float] = None
    # Metadata
    trading_days: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase insert."""
        return {
            "month": self.month,
            "symbol": self.symbol,
            "open_price": self.open_price,
            "close_price": self.close_price,
            "high_price": self.high_price,
            "low_price": self.low_price,
            "avg_price": self.avg_price,
            "avg_rsi": self.avg_rsi,
            "min_rsi": self.min_rsi,
            "max_rsi": self.max_rsi,
            "avg_stoch_k": self.avg_stoch_k,
            "avg_williams_r": self.avg_williams_r,
            "avg_macd": self.avg_macd,
            "avg_adx": self.avg_adx,
            "avg_bullish_score": self.avg_bullish_score,
            "max_bullish_score": self.max_bullish_score,
            "avg_reversal_score": self.avg_reversal_score,
            "max_reversal_score": self.max_reversal_score,
            "avg_oversold_score": self.avg_oversold_score,
            "max_oversold_score": self.max_oversold_score,
            "trading_days": self.trading_days,
        }


class MonthlyAggregator:
    """
    Aggregates daily indicators into monthly summaries.

    Storage tiers:
    - Tier 1 (Hot): 0-7 days - Raw JSON cache (007-ticker-analysis)
    - Tier 2 (Daily): 7-90 days - Full daily snapshots in Supabase
    - Tier 3 (Monthly): 90+ days - Compressed monthly aggregates
    """

    # Days to keep full daily data before aggregation
    RETENTION_DAYS = 90

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
    ):
        """Initialize the aggregator with Supabase credentials."""
        self.url = url or os.environ.get("SUPABASE_URL")
        self.key = key or os.environ.get("SUPABASE_SERVICE_KEY")
        self._client = None

    @property
    def client(self):
        """Lazy-load the Supabase client."""
        if self._client is None:
            if not self.url or not self.key:
                raise ValueError(
                    "Supabase credentials not configured. "
                    "Set SUPABASE_URL and SUPABASE_SERVICE_KEY."
                )
            from supabase import create_client
            self._client = create_client(self.url, self.key)
        return self._client

    @property
    def is_configured(self) -> bool:
        """Check if Supabase credentials are available."""
        return bool(self.url and self.key)

    def get_months_to_aggregate(self) -> List[str]:
        """
        Find months that have daily data older than retention period
        and haven't been aggregated yet.

        Returns:
            List of month strings (YYYY-MM) to aggregate
        """
        if not self.is_configured:
            return []

        cutoff_date = (date.today() - timedelta(days=self.RETENTION_DAYS)).isoformat()

        try:
            # Get distinct months from daily_indicators older than cutoff
            # that aren't in monthly_aggregates
            result = self.client.rpc(
                'get_unaggregated_months',
                {'cutoff_date': cutoff_date}
            ).execute()

            if result.data:
                return [r['month'] for r in result.data]
            return []
        except Exception as e:
            # If RPC doesn't exist, fall back to manual query
            logger.debug(f"RPC not available, using fallback: {e}")
            return self._get_months_fallback(cutoff_date)

    def _get_months_fallback(self, cutoff_date: str) -> List[str]:
        """Fallback method to find months needing aggregation."""
        try:
            # Get all dates older than cutoff
            daily_result = (
                self.client
                .table("daily_indicators")
                .select("date")
                .lt("date", cutoff_date)
                .execute()
            )

            if not daily_result.data:
                return []

            # Extract unique months
            daily_months = set()
            for row in daily_result.data:
                date_str = row['date']
                month = date_str[:7]  # YYYY-MM
                daily_months.add(month)

            # Get already aggregated months
            agg_result = (
                self.client
                .table("monthly_aggregates")
                .select("month")
                .execute()
            )

            agg_months = set()
            if agg_result.data:
                agg_months = {r['month'] for r in agg_result.data}

            # Return months that need aggregation
            return sorted(daily_months - agg_months)

        except Exception as e:
            logger.error(f"Failed to get months: {e}")
            return []

    def aggregate_month(self, month: str) -> int:
        """
        Aggregate daily data for a specific month into monthly summaries.

        Args:
            month: Month string in YYYY-MM format

        Returns:
            Number of symbol aggregates created
        """
        if not self.is_configured:
            return 0

        logger.info(f"Aggregating month: {month}")

        # Get all daily data for this month
        start_date = f"{month}-01"
        # Calculate end of month
        year, mon = int(month[:4]), int(month[5:7])
        if mon == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{mon + 1:02d}-01"

        try:
            result = (
                self.client
                .table("daily_indicators")
                .select("*")
                .gte("date", start_date)
                .lt("date", end_date)
                .order("date")
                .execute()
            )

            if not result.data:
                logger.info(f"No data found for {month}")
                return 0

            # Group by symbol
            by_symbol: Dict[str, List[Dict]] = {}
            for row in result.data:
                symbol = row['symbol']
                if symbol not in by_symbol:
                    by_symbol[symbol] = []
                by_symbol[symbol].append(row)

            # Create aggregates
            aggregates = []
            for symbol, rows in by_symbol.items():
                agg = self._create_aggregate(month, symbol, rows)
                aggregates.append(agg)

            # Upsert to monthly_aggregates
            records = [a.to_dict() for a in aggregates]
            self.client.table("monthly_aggregates").upsert(
                records,
                on_conflict="month,symbol"
            ).execute()

            logger.info(f"Created {len(aggregates)} aggregates for {month}")
            return len(aggregates)

        except Exception as e:
            logger.error(f"Failed to aggregate {month}: {e}")
            return 0

    def _create_aggregate(
        self,
        month: str,
        symbol: str,
        rows: List[Dict]
    ) -> MonthlyAggregate:
        """Create a monthly aggregate from daily rows."""
        # Sort by date to get first/last correctly
        rows = sorted(rows, key=lambda r: r['date'])

        # Price stats
        closes = [r['close'] for r in rows if r.get('close')]

        def safe_avg(values: List) -> Optional[float]:
            valid = [v for v in values if v is not None]
            return sum(valid) / len(valid) if valid else None

        def safe_min(values: List) -> Optional[float]:
            valid = [v for v in values if v is not None]
            return min(valid) if valid else None

        def safe_max(values: List) -> Optional[float]:
            valid = [v for v in values if v is not None]
            return max(valid) if valid else None

        # Extract indicator values
        rsi_vals = [r.get('rsi') for r in rows]
        stoch_vals = [r.get('stoch_k') for r in rows]
        williams_vals = [r.get('williams_r') for r in rows]
        macd_vals = [r.get('macd') for r in rows]
        adx_vals = [r.get('adx') for r in rows]
        bullish_vals = [r.get('bullish_score') for r in rows]
        reversal_vals = [r.get('reversal_score') for r in rows]
        oversold_vals = [r.get('oversold_score') for r in rows]

        return MonthlyAggregate(
            month=month,
            symbol=symbol,
            open_price=closes[0] if closes else 0,
            close_price=closes[-1] if closes else 0,
            high_price=safe_max(closes) or 0,
            low_price=safe_min(closes) or 0,
            avg_price=safe_avg(closes) or 0,
            avg_rsi=safe_avg(rsi_vals),
            min_rsi=safe_min(rsi_vals),
            max_rsi=safe_max(rsi_vals),
            avg_stoch_k=safe_avg(stoch_vals),
            avg_williams_r=safe_avg(williams_vals),
            avg_macd=safe_avg(macd_vals),
            avg_adx=safe_avg(adx_vals),
            avg_bullish_score=safe_avg(bullish_vals),
            max_bullish_score=safe_max(bullish_vals),
            avg_reversal_score=safe_avg(reversal_vals),
            max_reversal_score=safe_max(reversal_vals),
            avg_oversold_score=safe_avg(oversold_vals),
            max_oversold_score=safe_max(oversold_vals),
            trading_days=len(rows),
        )

    def cleanup_old_daily(self, month: str) -> int:
        """
        Delete daily records for a month after aggregation.

        Only deletes if the month has been successfully aggregated.

        Args:
            month: Month string in YYYY-MM format

        Returns:
            Number of records deleted
        """
        if not self.is_configured:
            return 0

        # Verify aggregation exists
        check = (
            self.client
            .table("monthly_aggregates")
            .select("month")
            .eq("month", month)
            .limit(1)
            .execute()
        )

        if not check.data:
            logger.warning(f"Cannot cleanup {month}: not yet aggregated")
            return 0

        start_date = f"{month}-01"
        year, mon = int(month[:4]), int(month[5:7])
        if mon == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{mon + 1:02d}-01"

        try:
            result = (
                self.client
                .table("daily_indicators")
                .delete()
                .gte("date", start_date)
                .lt("date", end_date)
                .execute()
            )

            # Count deleted (Supabase returns deleted rows)
            deleted = len(result.data) if result.data else 0
            logger.info(f"Deleted {deleted} daily records for {month}")
            return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup {month}: {e}")
            return 0

    def run_aggregation(self, cleanup: bool = True) -> Dict[str, int]:
        """
        Run full aggregation cycle.

        1. Find months older than 90 days needing aggregation
        2. Aggregate each month
        3. Optionally cleanup daily records

        Args:
            cleanup: If True, delete daily records after aggregation

        Returns:
            Dict with aggregation stats
        """
        if not self.is_configured:
            logger.warning("Supabase not configured, skipping aggregation")
            return {"months": 0, "aggregates": 0, "deleted": 0}

        months = self.get_months_to_aggregate()

        if not months:
            logger.info("No months need aggregation")
            return {"months": 0, "aggregates": 0, "deleted": 0}

        logger.info(f"Found {len(months)} months to aggregate: {months}")

        total_aggregates = 0
        total_deleted = 0

        for month in months:
            count = self.aggregate_month(month)
            total_aggregates += count

            if cleanup and count > 0:
                deleted = self.cleanup_old_daily(month)
                total_deleted += deleted

        return {
            "months": len(months),
            "aggregates": total_aggregates,
            "deleted": total_deleted,
        }


# Module-level convenience function
_aggregator: Optional[MonthlyAggregator] = None


def _get_aggregator() -> MonthlyAggregator:
    """Get or create the singleton aggregator instance."""
    global _aggregator
    if _aggregator is None:
        _aggregator = MonthlyAggregator()
    return _aggregator


def run_monthly_aggregation(cleanup: bool = True) -> Dict[str, int]:
    """
    Convenience function to run monthly aggregation.

    Args:
        cleanup: If True, delete old daily records after aggregation

    Returns:
        Dict with stats: {months, aggregates, deleted}
    """
    return _get_aggregator().run_aggregation(cleanup=cleanup)
