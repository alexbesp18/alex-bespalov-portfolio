"""
Supabase database operations for AA Points Monitor.
Cloud PostgreSQL backend with the same interface as SQLite database.py.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps
import time

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from config.settings import get_settings

logger = logging.getLogger(__name__)


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry Supabase operations on transient errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Supabase error (attempt {attempt + 1}): {e}")
                        time.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"Supabase error after {max_retries} attempts: {e}")
            raise last_error
        return wrapper
    return decorator


class SupabaseDatabase:
    """Supabase database wrapper with same interface as SQLite Database class."""

    def __init__(self):
        """Initialize Supabase connection."""
        settings = get_settings()

        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key,
            options=ClientOptions(schema='aa_scraper')
        )
        logger.info("Supabase client initialized with schema: aa_scraper")

    # ==================== SimplyMiles Operations ====================

    @retry_on_error()
    def insert_simplymiles_offer(
        self,
        merchant_name: str,
        merchant_name_normalized: str,
        offer_type: str,
        miles_amount: int,
        lp_amount: int,
        min_spend: Optional[float],
        expires_at: Optional[str],
        expiring_soon: bool,
        scraped_at: str
    ) -> str:
        """Insert a SimplyMiles offer. Returns UUID."""
        result = self.client.table('simplymiles_offers').insert({
            'merchant_name': merchant_name,
            'merchant_name_normalized': merchant_name_normalized,
            'offer_type': offer_type,
            'miles_amount': miles_amount,
            'lp_amount': lp_amount,
            'min_spend': min_spend,
            'expires_at': expires_at,
            'expiring_soon': expiring_soon,
            'scraped_at': scraped_at
        }).execute()

        return result.data[0]['id'] if result.data else None

    @retry_on_error()
    def get_active_simplymiles_offers(self) -> List[Dict[str, Any]]:
        """Get all non-expired SimplyMiles offers from the latest scrape."""
        # Get the latest scrape time
        latest_result = self.client.table('simplymiles_offers')\
            .select('scraped_at')\
            .order('scraped_at', desc=True)\
            .limit(1)\
            .execute()

        if not latest_result.data:
            return []

        latest_scraped = latest_result.data[0]['scraped_at']
        now = datetime.now().isoformat()

        # Get offers from latest scrape that haven't expired
        result = self.client.table('simplymiles_offers')\
            .select('*')\
            .eq('scraped_at', latest_scraped)\
            .or_(f'expires_at.is.null,expires_at.gt.{now}')\
            .order('miles_amount', desc=True)\
            .execute()

        return result.data or []

    @retry_on_error()
    def clear_simplymiles_offers(self):
        """Clear all SimplyMiles offers (before fresh scrape)."""
        # Count first for verification
        count_result = self.client.table('simplymiles_offers').select('id', count='exact').execute()
        before_count = count_result.count or 0

        if before_count > 0:
            # Delete all rows where id >= 0 (matches all positive integer IDs)
            self.client.table('simplymiles_offers').delete().gte('id', 0).execute()

            # Verify deletion
            verify_result = self.client.table('simplymiles_offers').select('id', count='exact').execute()
            after_count = verify_result.count or 0

            if after_count > 0:
                logger.warning(f"SimpleMiles clear incomplete: {after_count} rows remain")
            else:
                logger.info(f"Cleared {before_count} SimpleMiles offers")
        else:
            logger.info("SimpleMiles offers table already empty")

    # ==================== Portal Operations ====================

    @retry_on_error()
    def insert_portal_rate(
        self,
        merchant_name: str,
        merchant_name_normalized: str,
        miles_per_dollar: float,
        is_bonus_rate: bool,
        category: Optional[str],
        url: Optional[str],
        scraped_at: str
    ) -> str:
        """Insert a portal rate. Returns UUID."""
        result = self.client.table('portal_rates').insert({
            'merchant_name': merchant_name,
            'merchant_name_normalized': merchant_name_normalized,
            'miles_per_dollar': miles_per_dollar,
            'is_bonus_rate': is_bonus_rate,
            'category': category,
            'url': url,
            'scraped_at': scraped_at
        }).execute()

        return result.data[0]['id'] if result.data else None

    @retry_on_error()
    def get_latest_portal_rates(self) -> List[Dict[str, Any]]:
        """Get portal rates from the latest scrape."""
        # Get the latest scrape time
        latest_result = self.client.table('portal_rates')\
            .select('scraped_at')\
            .order('scraped_at', desc=True)\
            .limit(1)\
            .execute()

        if not latest_result.data:
            return []

        latest_scraped = latest_result.data[0]['scraped_at']

        result = self.client.table('portal_rates')\
            .select('*')\
            .eq('scraped_at', latest_scraped)\
            .order('miles_per_dollar', desc=True)\
            .execute()

        return result.data or []

    @retry_on_error()
    def clear_portal_rates(self):
        """Clear all portal rates (before fresh scrape)."""
        # Count first for verification
        count_result = self.client.table('portal_rates').select('id', count='exact').execute()
        before_count = count_result.count or 0

        if before_count > 0:
            # Delete all rows where id >= 0 (matches all positive integer IDs)
            self.client.table('portal_rates').delete().gte('id', 0).execute()

            # Verify deletion
            verify_result = self.client.table('portal_rates').select('id', count='exact').execute()
            after_count = verify_result.count or 0

            if after_count > 0:
                logger.warning(f"Portal rates clear incomplete: {after_count} rows remain")
            else:
                logger.info(f"Cleared {before_count} portal rates")
        else:
            logger.info("Portal rates table already empty")

    # ==================== Hotel Operations ====================

    @retry_on_error()
    def insert_hotel_deal(
        self,
        hotel_name: str,
        city: str,
        state: str,
        check_in: str,
        check_out: str,
        nightly_rate: float,
        base_miles: int,
        bonus_miles: int,
        total_miles: int,
        total_cost: float,
        yield_ratio: float,
        deal_score: float,
        url: Optional[str],
        scraped_at: str
    ) -> str:
        """Insert a hotel deal. Returns UUID."""
        result = self.client.table('hotel_deals').insert({
            'hotel_name': hotel_name,
            'city': city,
            'state': state,
            'check_in': check_in,
            'check_out': check_out,
            'nightly_rate': nightly_rate,
            'base_miles': base_miles,
            'bonus_miles': bonus_miles,
            'total_miles': total_miles,
            'total_cost': total_cost,
            'yield_ratio': yield_ratio,
            'deal_score': deal_score,
            'url': url,
            'scraped_at': scraped_at
        }).execute()

        return result.data[0]['id'] if result.data else None

    @retry_on_error()
    def get_top_hotel_deals(
        self,
        city: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top hotel deals, optionally filtered by city."""
        today = datetime.now().date().isoformat()

        query = self.client.table('hotel_deals')\
            .select('*')\
            .gt('check_in', today)\
            .order('deal_score', desc=True)\
            .limit(limit)

        if city:
            query = query.eq('city', city)

        result = query.execute()
        return result.data or []

    @retry_on_error()
    def clear_hotel_deals(self):
        """Clear all hotel deals (before fresh scrape)."""
        # Count first for verification
        count_result = self.client.table('hotel_deals').select('id', count='exact').execute()
        before_count = count_result.count or 0

        if before_count > 0:
            # Delete all rows where id >= 0 (matches all positive integer IDs)
            self.client.table('hotel_deals').delete().gte('id', 0).execute()

            # Verify deletion
            verify_result = self.client.table('hotel_deals').select('id', count='exact').execute()
            after_count = verify_result.count or 0

            if after_count > 0:
                logger.warning(f"Hotel deals clear incomplete: {after_count} rows remain")
            else:
                logger.info(f"Cleared {before_count} hotel deals")
        else:
            logger.info("Hotel deals table already empty")

    # ==================== Hotel Yield Baselines ====================

    @retry_on_error()
    def update_hotel_baseline(
        self,
        hotel_name: str,
        city: str,
        day_of_week: int,
        star_rating: int,
        yield_ratio: float
    ):
        """
        Update hotel yield baseline using Welford's online algorithm.
        Maintains running mean and variance without storing all observations.
        """
        now = datetime.now().isoformat()

        # Check for existing baseline
        result = self.client.table('hotel_yield_baselines')\
            .select('*')\
            .eq('hotel_name', hotel_name)\
            .eq('city', city)\
            .eq('day_of_week', day_of_week)\
            .execute()

        if result.data:
            existing = result.data[0]
            old_count = existing.get('observation_count', 1)
            old_avg = existing.get('avg_yield', yield_ratio)
            old_stddev = existing.get('stddev_yield', 0)
            old_min = existing.get('min_yield', yield_ratio)
            old_max = existing.get('max_yield', yield_ratio)

            # Welford's algorithm
            new_count = old_count + 1
            delta = yield_ratio - old_avg
            new_avg = old_avg + delta / new_count
            delta2 = yield_ratio - new_avg

            # Update variance (M2)
            old_m2 = (old_stddev ** 2) * old_count if old_count > 1 else 0
            new_m2 = old_m2 + delta * delta2
            new_stddev = (new_m2 / new_count) ** 0.5 if new_count > 1 else 0

            self.client.table('hotel_yield_baselines')\
                .update({
                    'avg_yield': new_avg,
                    'stddev_yield': new_stddev,
                    'min_yield': min(old_min, yield_ratio),
                    'max_yield': max(old_max, yield_ratio),
                    'observation_count': new_count,
                    'last_updated': now
                })\
                .eq('hotel_name', hotel_name)\
                .eq('city', city)\
                .eq('day_of_week', day_of_week)\
                .execute()
        else:
            # First observation
            self.client.table('hotel_yield_baselines').insert({
                'hotel_name': hotel_name,
                'city': city,
                'day_of_week': day_of_week,
                'star_rating': star_rating,
                'avg_yield': yield_ratio,
                'stddev_yield': 0,
                'min_yield': yield_ratio,
                'max_yield': yield_ratio,
                'observation_count': 1,
                'last_updated': now
            }).execute()

    @retry_on_error()
    def get_hotel_baseline(
        self,
        hotel_name: str,
        city: str,
        day_of_week: int
    ) -> Optional[Dict[str, Any]]:
        """Get the yield baseline for a specific hotel on a day of week."""
        result = self.client.table('hotel_yield_baselines')\
            .select('avg_yield, stddev_yield, min_yield, max_yield, observation_count, star_rating')\
            .eq('hotel_name', hotel_name)\
            .eq('city', city)\
            .eq('day_of_week', day_of_week)\
            .execute()

        return result.data[0] if result.data else None

    @retry_on_error()
    def get_city_star_tier_average(
        self,
        city: str,
        star_rating: int,
        day_of_week: Optional[int] = None
    ) -> Optional[float]:
        """Get average yield for a city/star/day combination."""
        query = self.client.table('hotel_yield_baselines')\
            .select('avg_yield')\
            .eq('city', city)\
            .eq('star_rating', star_rating)\
            .gte('observation_count', 3)

        if day_of_week is not None:
            query = query.eq('day_of_week', day_of_week)

        result = query.execute()

        if not result.data:
            return None

        yields = [r['avg_yield'] for r in result.data if r.get('avg_yield')]
        return sum(yields) / len(yields) if yields else None

    # ==================== Deal Discoveries ====================

    @retry_on_error()
    def upsert_discovery(
        self,
        deal_type: str,
        deal_identifier: str,
        yield_value: float
    ):
        """Track when a deal is first discovered."""
        now = datetime.now().isoformat()

        # Check if exists
        result = self.client.table('deal_discoveries')\
            .select('id, first_seen_at, times_seen, best_yield_seen')\
            .eq('deal_type', deal_type)\
            .eq('deal_identifier', deal_identifier)\
            .execute()

        if result.data:
            existing = result.data[0]
            self.client.table('deal_discoveries')\
                .update({
                    'last_seen_at': now,
                    'times_seen': (existing.get('times_seen', 1) or 1) + 1,
                    'best_yield_seen': max(
                        existing.get('best_yield_seen', 0) or 0,
                        yield_value
                    )
                })\
                .eq('id', existing['id'])\
                .execute()
        else:
            self.client.table('deal_discoveries').insert({
                'deal_type': deal_type,
                'deal_identifier': deal_identifier,
                'first_seen_at': now,
                'last_seen_at': now,
                'times_seen': 1,
                'best_yield_seen': yield_value
            }).execute()

    @retry_on_error()
    def get_new_discoveries(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get deals discovered in the last N days that are still active."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent_cutoff = (datetime.now() - timedelta(hours=48)).isoformat()

        result = self.client.table('deal_discoveries')\
            .select('deal_type, deal_identifier, first_seen_at, last_seen_at, times_seen, best_yield_seen')\
            .gte('first_seen_at', cutoff)\
            .gte('last_seen_at', recent_cutoff)\
            .order('first_seen_at', desc=True)\
            .execute()

        return result.data or []

    @retry_on_error()
    def is_new_discovery(self, deal_type: str, deal_identifier: str, days: int = 7) -> bool:
        """Check if a deal was first discovered within the last N days."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        result = self.client.table('deal_discoveries')\
            .select('first_seen_at')\
            .eq('deal_type', deal_type)\
            .eq('deal_identifier', deal_identifier)\
            .gte('first_seen_at', cutoff)\
            .execute()

        return bool(result.data)

    # ==================== Stacked Opportunities ====================

    @retry_on_error()
    def insert_stacked_opportunity(
        self,
        merchant_name: str,
        portal_rate: float,
        portal_miles: int,
        simplymiles_type: str,
        simplymiles_miles: int,
        simplymiles_min_spend: Optional[float],
        simplymiles_expires: Optional[str],
        cc_miles: int,
        min_spend_required: float,
        total_miles: int,
        combined_yield: float,
        deal_score: float,
        computed_at: str
    ) -> str:
        """Insert a stacked opportunity. Returns UUID."""
        result = self.client.table('stacked_opportunities').insert({
            'merchant_name': merchant_name,
            'portal_rate': portal_rate,
            'portal_miles': portal_miles,
            'simplymiles_type': simplymiles_type,
            'simplymiles_miles': simplymiles_miles,
            'simplymiles_min_spend': simplymiles_min_spend,
            'simplymiles_expires': simplymiles_expires,
            'cc_miles': cc_miles,
            'min_spend_required': min_spend_required,
            'total_miles': total_miles,
            'combined_yield': combined_yield,
            'deal_score': deal_score,
            'computed_at': computed_at
        }).execute()

        return result.data[0]['id'] if result.data else None

    @retry_on_error()
    def get_top_stacked_opportunities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top stacked opportunities by deal score."""
        # Get the latest computation time
        latest_result = self.client.table('stacked_opportunities')\
            .select('computed_at')\
            .order('computed_at', desc=True)\
            .limit(1)\
            .execute()

        if not latest_result.data:
            return []

        latest_computed = latest_result.data[0]['computed_at']
        now = datetime.now().isoformat()

        result = self.client.table('stacked_opportunities')\
            .select('*')\
            .eq('computed_at', latest_computed)\
            .or_(f'simplymiles_expires.is.null,simplymiles_expires.gt.{now}')\
            .order('deal_score', desc=True)\
            .limit(limit)\
            .execute()

        return result.data or []

    @retry_on_error()
    def clear_stacked_opportunities(self):
        """Clear stacked opportunities (before recomputation)."""
        # Count first for verification
        count_result = self.client.table('stacked_opportunities').select('id', count='exact').execute()
        before_count = count_result.count or 0

        if before_count > 0:
            # Delete all rows where id >= 0 (matches all positive integer IDs)
            self.client.table('stacked_opportunities').delete().gte('id', 0).execute()

            # Verify deletion
            verify_result = self.client.table('stacked_opportunities').select('id', count='exact').execute()
            after_count = verify_result.count or 0

            if after_count > 0:
                logger.warning(f"Stacked opportunities clear incomplete: {after_count} rows remain")
            else:
                logger.info(f"Cleared {before_count} stacked opportunities")
        else:
            logger.info("Stacked opportunities table already empty")

    # ==================== Alert History ====================

    @retry_on_error()
    def insert_alert(
        self,
        alert_type: str,
        deal_type: str,
        deal_identifier: str,
        deal_score: float,
        sent_at: str
    ) -> str:
        """Record an alert in history. Returns UUID."""
        result = self.client.table('alert_history').insert({
            'alert_type': alert_type,
            'deal_type': deal_type,
            'deal_identifier': deal_identifier,
            'deal_score': deal_score,
            'sent_at': sent_at
        }).execute()

        return result.data[0]['id'] if result.data else None

    @retry_on_error()
    def was_recently_alerted(
        self,
        deal_identifier: str,
        cooldown_hours: int = 24
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if a deal was recently alerted.

        Returns:
            (was_alerted, previous_score) - previous_score is None if not alerted
        """
        cutoff = (datetime.now() - timedelta(hours=cooldown_hours)).isoformat()

        result = self.client.table('alert_history')\
            .select('deal_score')\
            .eq('deal_identifier', deal_identifier)\
            .gt('sent_at', cutoff)\
            .order('sent_at', desc=True)\
            .limit(1)\
            .execute()

        if result.data:
            return True, result.data[0]['deal_score']
        return False, None

    # ==================== Scraper Health ====================

    @retry_on_error()
    def record_scraper_run(
        self,
        scraper_name: str,
        status: str,
        error_message: Optional[str] = None,
        items_scraped: int = 0,
        duration_seconds: Optional[float] = None
    ):
        """Record a scraper run for health monitoring."""
        self.client.table('scraper_health').insert({
            'scraper_name': scraper_name,
            'status': status,
            'error_message': error_message,
            'items_scraped': items_scraped,
            'duration_seconds': duration_seconds,
            'run_at': datetime.now().isoformat()
        }).execute()

    @retry_on_error()
    def get_consecutive_failures(self, scraper_name: str) -> int:
        """Get count of consecutive failures for a scraper."""
        result = self.client.table('scraper_health')\
            .select('status')\
            .eq('scraper_name', scraper_name)\
            .order('run_at', desc=True)\
            .limit(10)\
            .execute()

        failures = 0
        for row in result.data or []:
            if row['status'] == 'success':
                break
            failures += 1

        return failures

    @retry_on_error()
    def get_last_successful_scrape(self, scraper_name: str) -> Optional[str]:
        """Get timestamp of last successful scrape."""
        result = self.client.table('scraper_health')\
            .select('run_at')\
            .eq('scraper_name', scraper_name)\
            .eq('status', 'success')\
            .order('run_at', desc=True)\
            .limit(1)\
            .execute()

        return result.data[0]['run_at'] if result.data else None

    # ==================== Staleness Detection ====================

    @retry_on_error()
    def get_latest_scrape_time(self, source: str) -> Optional[datetime]:
        """Get the latest scrape time for a data source."""
        table_map = {
            'simplymiles': 'simplymiles_offers',
            'portal': 'portal_rates',
            'hotels': 'hotel_deals'
        }

        if source not in table_map:
            raise ValueError(f"Unknown source: {source}")

        result = self.client.table(table_map[source])\
            .select('scraped_at')\
            .order('scraped_at', desc=True)\
            .limit(1)\
            .execute()

        if result.data and result.data[0]['scraped_at']:
            ts = result.data[0]['scraped_at']
            # Handle ISO format with Z suffix (UTC)
            if ts.endswith('Z'):
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
            return datetime.fromisoformat(ts)
        return None

    @retry_on_error()
    def is_data_stale(self, source: str) -> bool:
        """Check if data from a source is stale based on configured thresholds."""
        settings = get_settings()

        thresholds = {
            'simplymiles': settings.scraper.simplymiles_stale_hours,
            'portal': settings.scraper.portal_stale_hours,
            'hotels': settings.scraper.hotels_stale_hours
        }

        if source not in thresholds:
            raise ValueError(f"Unknown source: {source}")

        latest = self.get_latest_scrape_time(source)
        if latest is None:
            return True

        age_hours = (datetime.now() - latest).total_seconds() / 3600
        return age_hours > thresholds[source]

    @retry_on_error()
    def get_data_freshness_report(self) -> Dict[str, Dict[str, Any]]:
        """Get a report on data freshness for all sources."""
        sources = ['simplymiles', 'portal', 'hotels']
        report = {}

        for source in sources:
            latest = self.get_latest_scrape_time(source)
            is_stale = self.is_data_stale(source)

            if latest:
                age_hours = (datetime.now() - latest).total_seconds() / 3600
            else:
                age_hours = None

            report[source] = {
                'latest_scrape': latest.isoformat() if latest else None,
                'age_hours': round(age_hours, 1) if age_hours else None,
                'is_stale': is_stale
            }

        return report

    # ==================== Hotel Yield History ====================

    @retry_on_error()
    def record_hotel_yield(
        self,
        city: str,
        day_of_week: int,
        advance_days: int,
        avg_yield: float,
        max_yield: float,
        deal_count: int
    ):
        """Record historical hotel yield data for adaptive scanning."""
        # For Supabase, update the merchant_history table with hotel yield data
        today = datetime.now().date().isoformat()

        self.client.table('merchant_history').upsert({
            'merchant_name_normalized': f"hotel_{city}_{day_of_week}_{advance_days}",
            'recorded_date': today,
            'stacked_yield': avg_yield
        }, on_conflict='merchant_name_normalized,recorded_date').execute()

    @retry_on_error()
    def get_historical_yields(
        self,
        city: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get historical yield data for a city."""
        cutoff = (datetime.now() - timedelta(days=days_back)).date().isoformat()

        result = self.client.table('merchant_history')\
            .select('*')\
            .like('merchant_name_normalized', f'hotel_{city}_%')\
            .gt('recorded_date', cutoff)\
            .order('stacked_yield', desc=True)\
            .execute()

        return result.data or []

    @retry_on_error()
    def get_best_yield_slots(
        self,
        city: str,
        limit: int = 10,
        min_deals: int = 2
    ) -> List[Dict[str, Any]]:
        """Get the historically best-yielding (day_of_week, advance_days) combinations."""
        # Use yield matrix for this
        result = self.client.table('hotel_yield_matrix')\
            .select('day_of_week, advance_days, avg_yield, max_yield, deal_count')\
            .eq('city', city)\
            .gte('deal_count', min_deals)\
            .order('avg_yield', desc=True)\
            .limit(limit)\
            .execute()

        return result.data or []

    @retry_on_error()
    def get_yield_prediction(
        self,
        city: str,
        day_of_week: int,
        advance_days: int
    ) -> Optional[float]:
        """Predict expected yield for a specific (city, day_of_week, advance_days) combo."""
        # Look for entries within +-7 days of advance_days
        result = self.client.table('hotel_yield_matrix')\
            .select('avg_yield')\
            .eq('city', city)\
            .eq('day_of_week', day_of_week)\
            .gte('advance_days', advance_days - 7)\
            .lte('advance_days', advance_days + 7)\
            .order('avg_yield', desc=True)\
            .limit(1)\
            .execute()

        return result.data[0]['avg_yield'] if result.data else None

    # ==================== Hotel Yield Matrix ====================

    @retry_on_error()
    def upsert_yield_matrix_entry(
        self,
        city: str,
        day_of_week: int,
        duration: int,
        advance_days: int,
        stats: Dict[str, Any],
        top_premium: Optional[Dict[str, Any]] = None,
        top_budget: Optional[Dict[str, Any]] = None
    ):
        """Insert or update a yield matrix entry."""
        now = datetime.now().isoformat()

        # Check if entry exists
        existing = self.client.table('hotel_yield_matrix')\
            .select('id, verification_count, avg_yield, yield_stability')\
            .eq('city', city)\
            .eq('day_of_week', day_of_week)\
            .eq('duration', duration)\
            .eq('advance_days', advance_days)\
            .execute()

        data = {
            'city': city,
            'day_of_week': day_of_week,
            'duration': duration,
            'advance_days': advance_days,
            'avg_yield': stats.get('avg_yield'),
            'max_yield': stats.get('max_yield'),
            'min_yield': stats.get('min_yield'),
            'median_yield': stats.get('median_yield'),
            'deal_count': stats.get('deal_count', 0),
            'last_verified_at': now
        }

        # Add top hotel data as JSONB
        if top_premium:
            data['top_premium_hotel'] = top_premium
        if top_budget:
            data['top_budget_hotel'] = top_budget

        if existing.data:
            # Update existing entry
            entry = existing.data[0]
            old_yield = entry.get('avg_yield') or 0
            new_yield = stats.get('avg_yield', 0)
            ver_count = (entry.get('verification_count') or 0) + 1

            # Calculate stability
            if old_yield > 0 and new_yield > 0:
                drift = abs(new_yield - old_yield) / old_yield
                old_stability = entry.get('yield_stability') or 1.0
                stability = 0.7 * old_stability + 0.3 * (1.0 - min(drift, 1.0))
            else:
                stability = entry.get('yield_stability')

            data['verification_count'] = ver_count
            data['yield_stability'] = stability

            self.client.table('hotel_yield_matrix')\
                .update(data)\
                .eq('id', entry['id'])\
                .execute()
        else:
            # Insert new entry
            data['discovered_at'] = now
            data['verification_count'] = 1

            self.client.table('hotel_yield_matrix').insert(data).execute()

    @retry_on_error()
    def get_matrix_entry(
        self,
        city: str,
        day_of_week: int,
        duration: int,
        advance_days: int
    ) -> Optional[Dict[str, Any]]:
        """Get a specific yield matrix entry."""
        result = self.client.table('hotel_yield_matrix')\
            .select('*')\
            .eq('city', city)\
            .eq('day_of_week', day_of_week)\
            .eq('duration', duration)\
            .eq('advance_days', advance_days)\
            .execute()

        return result.data[0] if result.data else None

    @retry_on_error()
    def get_top_matrix_entries(
        self,
        city: Optional[str] = None,
        min_stars: int = 4,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get top yield matrix entries."""
        query = self.client.table('hotel_yield_matrix')\
            .select('*')\
            .gt('deal_count', 0)\
            .order('avg_yield', desc=True)\
            .limit(limit)

        if city:
            query = query.eq('city', city)

        result = query.execute()
        return result.data or []

    @retry_on_error()
    def get_unexplored_combinations(
        self,
        cities: List[str],
        days_of_week: List[int],
        durations: List[int],
        advance_days_options: List[int]
    ) -> List[Tuple[str, int, int, int]]:
        """Get combinations not yet in the matrix."""
        # Get all existing combinations
        result = self.client.table('hotel_yield_matrix')\
            .select('city, day_of_week, duration, advance_days')\
            .execute()

        existing = set()
        for row in result.data or []:
            existing.add((row['city'], row['day_of_week'], row['duration'], row['advance_days']))

        # Find unexplored
        unexplored = []
        for city in cities:
            for dow in days_of_week:
                for dur in durations:
                    for adv in advance_days_options:
                        key = (city, dow, dur, adv)
                        if key not in existing:
                            unexplored.append(key)

        return unexplored

    @retry_on_error()
    def get_stale_matrix_entries(
        self,
        days_old: int = 7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get matrix entries that haven't been verified recently."""
        cutoff = (datetime.now() - timedelta(days=days_old)).isoformat()

        result = self.client.table('hotel_yield_matrix')\
            .select('*')\
            .or_(f'last_verified_at.lt.{cutoff},last_verified_at.is.null')\
            .order('last_verified_at', nullsfirst=True)\
            .limit(limit)\
            .execute()

        return result.data or []

    @retry_on_error()
    def get_matrix_stats(self) -> Dict[str, Any]:
        """Get overall statistics about the yield matrix."""
        result = self.client.table('hotel_yield_matrix')\
            .select('*')\
            .execute()

        data = result.data or []
        if not data:
            return {}

        entries_with_data = [d for d in data if d.get('deal_count', 0) > 0]
        yields = [d['avg_yield'] for d in entries_with_data if d.get('avg_yield')]
        max_yields = [d['max_yield'] for d in entries_with_data if d.get('max_yield')]
        ver_counts = [d.get('verification_count', 1) for d in data]

        return {
            'total_entries': len(data),
            'entries_with_data': len(entries_with_data),
            'overall_avg_yield': sum(yields) / len(yields) if yields else None,
            'best_yield_ever': max(max_yields) if max_yields else None,
            'avg_verifications': sum(ver_counts) / len(ver_counts) if ver_counts else None
        }

    # ==================== Matrix-Aware Date Selection ====================

    @retry_on_error()
    def get_best_matrix_slots(
        self,
        city: str,
        duration: int = 1,
        limit: int = 20,
        min_stability: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Get the best-yielding slots from the yield matrix."""
        result = self.client.table('hotel_yield_matrix')\
            .select('day_of_week, advance_days, avg_yield, max_yield, deal_count, yield_stability, top_premium_hotel, top_budget_hotel')\
            .eq('city', city)\
            .eq('duration', duration)\
            .gt('deal_count', 0)\
            .or_(f'yield_stability.gte.{min_stability},yield_stability.is.null')\
            .order('avg_yield', desc=True)\
            .limit(limit)\
            .execute()

        return result.data or []

    @retry_on_error()
    def get_matrix_yield_prediction(
        self,
        city: str,
        day_of_week: int,
        duration: int,
        advance_days: int
    ) -> Optional[Dict[str, Any]]:
        """Get yield prediction from the matrix for a specific combination."""
        # Try exact match first
        result = self.client.table('hotel_yield_matrix')\
            .select('avg_yield, max_yield, deal_count, yield_stability')\
            .eq('city', city)\
            .eq('day_of_week', day_of_week)\
            .eq('duration', duration)\
            .eq('advance_days', advance_days)\
            .execute()

        if result.data and result.data[0].get('avg_yield'):
            return result.data[0]

        # Find closest advance_days match
        result = self.client.table('hotel_yield_matrix')\
            .select('avg_yield, max_yield, deal_count, yield_stability, advance_days')\
            .eq('city', city)\
            .eq('day_of_week', day_of_week)\
            .eq('duration', duration)\
            .gt('deal_count', 0)\
            .execute()

        if not result.data:
            return None

        # Find closest by advance_days
        closest = min(result.data, key=lambda x: abs(x['advance_days'] - advance_days))
        return closest if closest.get('avg_yield') else None

    def get_priority_search_dates(
        self,
        city: str,
        duration: int = 1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get prioritized search dates for a city based on matrix data."""
        slots = self.get_best_matrix_slots(city, duration, limit * 2)

        scored = []
        for slot in slots:
            stability = slot.get('yield_stability') or 0.8
            expected = slot['avg_yield'] * (0.5 + 0.5 * stability)
            scored.append({
                'day_of_week': slot['day_of_week'],
                'advance_days': slot['advance_days'],
                'expected_yield': expected,
                'avg_yield': slot['avg_yield'],
                'max_yield': slot['max_yield'],
                'confidence': stability
            })

        scored.sort(key=lambda x: x['expected_yield'], reverse=True)
        return scored[:limit]

    # ==================== Analytics Tables ====================

    @retry_on_error()
    def upsert_daily_snapshot(self, snapshot_date: str, data: Dict[str, Any]):
        """Insert or update a daily snapshot."""
        data['snapshot_date'] = snapshot_date

        self.client.table('daily_snapshots').upsert(
            data, on_conflict='snapshot_date'
        ).execute()

    @retry_on_error()
    def get_daily_snapshots(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get recent daily snapshots for trend analysis."""
        cutoff = (datetime.now() - timedelta(days=days_back)).date().isoformat()

        result = self.client.table('daily_snapshots')\
            .select('*')\
            .gte('snapshot_date', cutoff)\
            .order('snapshot_date', desc=True)\
            .execute()

        return result.data or []

    @retry_on_error()
    def upsert_merchant_history(
        self,
        merchant_name_normalized: str,
        recorded_date: str,
        data: Dict[str, Any]
    ):
        """Insert or update merchant history entry."""
        data['merchant_name_normalized'] = merchant_name_normalized
        data['recorded_date'] = recorded_date

        self.client.table('merchant_history').upsert(
            data, on_conflict='merchant_name_normalized,recorded_date'
        ).execute()

    @retry_on_error()
    def get_merchant_history(
        self,
        merchant_name_normalized: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get history for a specific merchant."""
        cutoff = (datetime.now() - timedelta(days=days_back)).date().isoformat()

        result = self.client.table('merchant_history')\
            .select('*')\
            .eq('merchant_name_normalized', merchant_name_normalized)\
            .gte('recorded_date', cutoff)\
            .order('recorded_date', desc=True)\
            .execute()

        return result.data or []

    # ==================== Intelligence Tables ====================

    @retry_on_error()
    def insert_detected_pattern(self, pattern: Dict[str, Any]) -> str:
        """Insert a detected pattern."""
        pattern['first_observed'] = datetime.now().isoformat()
        pattern['last_observed'] = datetime.now().isoformat()
        pattern['is_active'] = True

        result = self.client.table('detected_patterns').insert(pattern).execute()
        return result.data[0]['id'] if result.data else None

    @retry_on_error()
    def get_active_patterns(
        self,
        pattern_type: Optional[str] = None,
        entity_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active detected patterns."""
        query = self.client.table('detected_patterns')\
            .select('*')\
            .eq('is_active', True)\
            .order('confidence_score', desc=True)

        if pattern_type:
            query = query.eq('pattern_type', pattern_type)
        if entity_name:
            query = query.eq('entity_name', entity_name)

        result = query.execute()
        return result.data or []

    @retry_on_error()
    def get_upcoming_predictions(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get predictions for the next N days."""
        now = datetime.now().isoformat()
        future = (datetime.now() + timedelta(days=days_ahead)).isoformat()

        result = self.client.table('predictive_alerts')\
            .select('*')\
            .gte('predicted_for', now)\
            .lte('predicted_for', future)\
            .eq('notified', False)\
            .order('predicted_for')\
            .execute()

        return result.data or []

    @retry_on_error()
    def insert_predictive_alert(self, alert: Dict[str, Any]) -> str:
        """Insert a predictive alert."""
        result = self.client.table('predictive_alerts').insert(alert).execute()
        return result.data[0]['id'] if result.data else None

    @retry_on_error()
    def upsert_status_progress(self, recorded_date: str, data: Dict[str, Any]):
        """Insert or update status progress."""
        data['recorded_date'] = recorded_date

        self.client.table('status_progress').upsert(
            data, on_conflict='recorded_date'
        ).execute()

    @retry_on_error()
    def get_status_progress(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get recent status progress entries."""
        cutoff = (datetime.now() - timedelta(days=days_back)).date().isoformat()

        result = self.client.table('status_progress')\
            .select('*')\
            .gte('recorded_date', cutoff)\
            .order('recorded_date', desc=True)\
            .execute()

        return result.data or []

    @retry_on_error()
    def get_cc_comparison_rates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get credit card comparison rates."""
        query = self.client.table('cc_comparison_rates').select('*')

        if category:
            query = query.eq('category', category)

        result = query.order('effective_rate', desc=True).execute()
        return result.data or []

    # ==================== Discovery Progress ====================

    @retry_on_error()
    def record_discovery_attempt(
        self,
        session_id: str,
        city: str,
        day_of_week: int,
        duration: int,
        advance_days: int,
        status: str,
        hotels_found: int = 0,
        error_message: Optional[str] = None
    ):
        """Record a discovery attempt for progress tracking."""
        now = datetime.now().isoformat()

        self.client.table('discovery_progress').insert({
            'session_id': session_id,
            'city': city,
            'day_of_week': day_of_week,
            'duration': duration,
            'advance_days': advance_days,
            'status': status,
            'hotels_found': hotels_found,
            'error_message': error_message,
            'started_at': now,
            'completed_at': now
        }).execute()

    @retry_on_error()
    def get_discovery_progress(self, session_id: str) -> Dict[str, Any]:
        """Get progress stats for a discovery session."""
        result = self.client.rpc('get_discovery_stats', {'p_session_id': session_id}).execute()

        if result.data:
            return result.data[0]

        # Fallback: manual query if RPC doesn't exist
        result = self.client.table('discovery_progress')\
            .select('*')\
            .eq('session_id', session_id)\
            .execute()

        if not result.data:
            return {}

        rows = result.data
        return {
            'total_attempts': len(rows),
            'successful': sum(1 for r in rows if r.get('status') == 'success'),
            'errors': sum(1 for r in rows if r.get('status') == 'error'),
            'total_hotels_found': sum(r.get('hotels_found', 0) for r in rows),
            'started': min(r.get('started_at', '') for r in rows) if rows else None,
            'last_update': max(r.get('completed_at', '') for r in rows) if rows else None
        }

    @retry_on_error()
    def get_completed_combinations(self, session_id: str) -> set:
        """Get set of combinations already completed in this session."""
        result = self.client.table('discovery_progress')\
            .select('city, day_of_week, duration, advance_days')\
            .eq('session_id', session_id)\
            .eq('status', 'success')\
            .execute()

        return {(row['city'], row['day_of_week'], row['duration'], row['advance_days'])
                for row in (result.data or [])}


# Singleton instance
_supabase_db: Optional[SupabaseDatabase] = None


def get_supabase_database() -> SupabaseDatabase:
    """Get the Supabase database singleton."""
    global _supabase_db
    if _supabase_db is None:
        _supabase_db = SupabaseDatabase()
    return _supabase_db
