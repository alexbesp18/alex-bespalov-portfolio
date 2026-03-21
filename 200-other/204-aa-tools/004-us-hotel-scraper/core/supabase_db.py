"""
Supabase database layer for US Hotel Scraper.
Cloud PostgreSQL backend with same interface as SQLite database.py.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
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
            options=ClientOptions(schema='us_hotels')
        )
        logger.info("Supabase client initialized with schema: us_hotels")

    # ==================== City Operations ====================

    @retry_on_error()
    def upsert_city(
        self,
        msa_name: str,
        city_name: str,
        state: str,
        agoda_place_id: Optional[str] = None,
        population: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> int:
        """Insert or update a city, return city ID."""
        data = {
            'msa_name': msa_name,
            'city_name': city_name,
            'state': state,
            'agoda_place_id': agoda_place_id,
            'population': population,
        }

        result = self.client.table('us_hotel_cities').upsert(
            data, on_conflict='msa_name'
        ).execute()

        return result.data[0]['id'] if result.data else None

    @retry_on_error()
    def get_active_cities(self) -> List[Dict[str, Any]]:
        """Get all active cities with Agoda place IDs."""
        result = self.client.table('us_hotel_cities')\
            .select('*')\
            .eq('is_active', True)\
            .not_.is_('agoda_place_id', 'null')\
            .order('population', desc=True, nullsfirst=False)\
            .execute()

        return result.data or []

    @retry_on_error()
    def get_city_by_id(self, city_id: int) -> Optional[Dict[str, Any]]:
        """Get a city by ID."""
        result = self.client.table('us_hotel_cities')\
            .select('*')\
            .eq('id', city_id)\
            .execute()

        return result.data[0] if result.data else None

    @retry_on_error()
    def get_city_by_name(self, city_name: str, state: str) -> Optional[Dict[str, Any]]:
        """Get a city by name and state."""
        result = self.client.table('us_hotel_cities')\
            .select('*')\
            .eq('city_name', city_name)\
            .eq('state', state)\
            .execute()

        return result.data[0] if result.data else None

    @retry_on_error()
    def update_city_last_scraped(self, city_id: int) -> None:
        """Mark a city as scraped now (checkpoint)."""
        self.client.table('us_hotel_cities').update({
            'last_scraped_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', city_id).execute()
        logger.debug(f"Checkpointed city {city_id} as scraped")

    @retry_on_error()
    def get_cities_needing_scrape(self, max_age_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get cities that need to be scraped (not scraped within max_age_hours).

        Used for checkpoint/resume - returns cities where:
        - last_scraped_at is NULL (never scraped), OR
        - last_scraped_at is older than max_age_hours
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).isoformat()

        result = self.client.table('us_hotel_cities')\
            .select('*')\
            .eq('is_active', True)\
            .not_.is_('agoda_place_id', 'null')\
            .or_(f'last_scraped_at.is.null,last_scraped_at.lt.{cutoff}')\
            .order('population', desc=True, nullsfirst=False)\
            .execute()

        return result.data or []

    # ==================== Hotel Operations ====================

    @retry_on_error()
    def upsert_hotel(
        self,
        hotel_name: str,
        city_id: int,
        stars: int = 0,
        rating: float = 0,
        review_count: int = 0,
        neighborhood: Optional[str] = None,
        agoda_hotel_id: Optional[str] = None,
    ) -> int:
        """Insert or update a hotel, return hotel ID."""
        # Check if exists
        existing = self.client.table('us_hotels')\
            .select('id')\
            .eq('hotel_name', hotel_name)\
            .eq('city_id', city_id)\
            .execute()

        if existing.data:
            # Update
            self.client.table('us_hotels')\
                .update({
                    'stars': stars,
                    'rating': rating,
                    'review_count': review_count,
                    'neighborhood': neighborhood,
                    'agoda_hotel_id': agoda_hotel_id,
                })\
                .eq('id', existing.data[0]['id'])\
                .execute()
            return existing.data[0]['id']
        else:
            # Insert
            result = self.client.table('us_hotels').insert({
                'hotel_name': hotel_name,
                'city_id': city_id,
                'stars': stars,
                'rating': rating,
                'review_count': review_count,
                'neighborhood': neighborhood,
                'agoda_hotel_id': agoda_hotel_id,
            }).execute()
            return result.data[0]['id'] if result.data else None

    # ==================== Deal Operations ====================

    @retry_on_error()
    def insert_deal(
        self,
        hotel_id: int,
        check_in: str,
        check_out: str,
        total_cost: float,
        total_miles: int,
        yield_ratio: float,
        deal_score: float,
        scrape_run_id: Optional[int] = None,
        nightly_rate: Optional[float] = None,
        base_miles: Optional[int] = None,
        bonus_miles: int = 0,
        room_type: Optional[str] = None,
        url: Optional[str] = None,
        adults: int = 2,
    ) -> Optional[int]:
        """Insert a hotel deal with configurable retention mode.

        If deal_retention_mode='best': Only keeps the best yield per (hotel, check_in, check_out).
        If deal_retention_mode='all': Keeps all deals (duplicates allowed).

        Returns:
            Deal ID if inserted/updated, None if skipped (existing deal is better or equal).
        """
        settings = get_settings()

        # BUG 4 FIX: Parse dates properly to handle timezone strings
        # Handle various date formats: "2025-01-18", "2025-01-18T00:00:00", "2025-01-18T00:00:00Z"
        if isinstance(check_in, str):
            # Normalize timezone suffix for fromisoformat
            check_in_clean = check_in.replace('Z', '+00:00')
            try:
                check_in_dt = datetime.fromisoformat(check_in_clean)
            except ValueError:
                # Fallback: just take first 10 chars as date
                check_in_dt = datetime.strptime(check_in[:10], '%Y-%m-%d')
        else:
            check_in_dt = check_in

        if isinstance(check_out, str):
            check_out_clean = check_out.replace('Z', '+00:00')
            try:
                check_out_dt = datetime.fromisoformat(check_out_clean)
            except ValueError:
                check_out_dt = datetime.strptime(check_out[:10], '%Y-%m-%d')
        else:
            check_out_dt = check_out

        # Now format as YYYY-MM-DD strings for storage/comparison
        check_in_str = check_in_dt.strftime('%Y-%m-%d')
        check_out_str = check_out_dt.strftime('%Y-%m-%d')

        nights = (check_out_dt.date() - check_in_dt.date()).days if hasattr(check_out_dt, 'date') else (check_out_dt - check_in_dt).days

        if nightly_rate is None:
            nightly_rate = total_cost / nights if nights > 0 else total_cost
        if base_miles is None:
            base_miles = total_miles

        # Use timezone-aware timestamp
        now = datetime.now(timezone.utc).isoformat()

        deal_data = {
            'hotel_id': hotel_id,
            'scrape_run_id': scrape_run_id,
            'check_in': check_in_str,
            'check_out': check_out_str,
            'nights': nights,
            'adults': adults,
            'nightly_rate': nightly_rate,
            'total_cost': total_cost,
            'base_miles': base_miles,
            'bonus_miles': bonus_miles,
            'total_miles': total_miles,
            'yield_ratio': yield_ratio,
            'deal_score': deal_score,
            'room_type': room_type,
            'url': url,
            'scraped_at': now,
        }

        # Check retention mode
        if settings.deal_retention_mode == "best":
            # Check if deal exists for this (hotel_id, check_in, check_out)
            existing = self.client.table('us_hotel_deals')\
                .select('id, yield_ratio')\
                .eq('hotel_id', hotel_id)\
                .eq('check_in', check_in_str)\
                .eq('check_out', check_out_str)\
                .execute()

            if existing.data:
                existing_yield = existing.data[0]['yield_ratio']
                existing_id = existing.data[0]['id']

                if yield_ratio > existing_yield:
                    # New is better - UPDATE existing record
                    update_result = self.client.table('us_hotel_deals')\
                        .update(deal_data)\
                        .eq('id', existing_id)\
                        .execute()
                    # Verify update succeeded
                    if update_result.data:
                        logger.debug(f"Updated deal {existing_id}: {existing_yield:.1f} -> {yield_ratio:.1f} LP/$")
                        return existing_id
                    else:
                        logger.warning(f"Update failed for deal {existing_id}, row may have been deleted")
                        # Fall through to insert
                elif yield_ratio == existing_yield:
                    # BUG 6 FIX: Explicit logging for equal yield case
                    logger.debug(f"Skipped deal: equal yield {yield_ratio:.1f} LP/$, keeping existing id={existing_id}")
                    return None
                else:
                    # Existing is better - SKIP
                    logger.debug(f"Skipped deal: existing {existing_yield:.1f} > new {yield_ratio:.1f} LP/$")
                    return None

        # Mode is 'all' OR no existing deal - INSERT new record
        result = self.client.table('us_hotel_deals').insert(deal_data).execute()
        return result.data[0]['id'] if result.data else None

    @retry_on_error()
    def get_top_deals(
        self,
        limit: int = 100,
        min_yield: float = 0,
        min_stars: int = 1,
        max_stars: int = 5,
        city_id: Optional[int] = None,
        city_ids: Optional[List[int]] = None,
        exclude_cities: bool = False,
        check_in_start: Optional[str] = None,
        check_in_end: Optional[str] = None,
        order_by: str = "yield_ratio",
    ) -> List[Dict[str, Any]]:
        """Get top deals with filters.

        Args:
            city_id: Single city ID (legacy, for backward compatibility)
            city_ids: List of city IDs for multiselect filtering
            exclude_cities: If True, exclude the city_ids; if False, include only those cities
        """
        today = datetime.now().date().isoformat()

        # Build query with joins
        query = self.client.table('us_hotel_deals')\
            .select('''
                id, check_in, check_out, nights, adults,
                nightly_rate, total_cost, total_miles,
                yield_ratio, deal_score, url, scraped_at,
                us_hotels!inner(hotel_name, stars, rating, review_count, neighborhood, city_id,
                    us_hotel_cities(city_name, state, msa_name))
            ''')\
            .gte('yield_ratio', min_yield)\
            .gte('check_in', today)

        # Handle city filtering (new multiselect takes precedence)
        if city_ids:
            if exclude_cities:
                # NOT IN - show all except these cities
                query = query.not_.in_('us_hotels.city_id', city_ids)
            else:
                # IN - show only these cities
                query = query.in_('us_hotels.city_id', city_ids)
        elif city_id:
            # Legacy single city filter
            query = query.eq('us_hotels.city_id', city_id)

        if check_in_start:
            query = query.gte('check_in', check_in_start)

        if check_in_end:
            query = query.lte('check_in', check_in_end)

        # Order by
        order_column = {
            "yield_ratio": "yield_ratio",
            "deal_score": "deal_score",
            "total_cost": "total_cost",
            "check_in": "check_in",
        }.get(order_by, "yield_ratio")

        desc = order_by not in ["total_cost", "check_in"]
        query = query.order(order_column, desc=desc).limit(limit)

        result = query.execute()

        # Flatten the nested structure
        deals = []
        for row in result.data or []:
            hotel = row.get('us_hotels', {})
            city = hotel.get('us_hotel_cities', {}) if hotel else {}
            deals.append({
                'id': row['id'],
                'check_in': row['check_in'],
                'check_out': row['check_out'],
                'nights': row['nights'],
                'adults': row.get('adults', 2),
                'nightly_rate': row['nightly_rate'],
                'total_cost': row['total_cost'],
                'total_miles': row['total_miles'],
                'yield_ratio': row['yield_ratio'],
                'deal_score': row['deal_score'],
                'url': row['url'],
                'scraped_at': row['scraped_at'],
                'hotel_name': hotel.get('hotel_name', ''),
                'stars': hotel.get('stars', 0),
                'rating': hotel.get('rating', 0),
                'review_count': hotel.get('review_count', 0),
                'neighborhood': hotel.get('neighborhood', ''),
                'city_name': city.get('city_name', ''),
                'state': city.get('state', ''),
                'msa_name': city.get('msa_name', ''),
            })

        return deals

    @retry_on_error()
    def clear_old_deals(self, days_old: int = 7):
        """Delete deals with check_in dates in the past."""
        cutoff = datetime.now().date().isoformat()

        result = self.client.table('us_hotel_deals')\
            .delete()\
            .lt('check_in', cutoff)\
            .execute()

        deleted = len(result.data) if result.data else 0
        logger.info(f"Deleted {deleted} old deals")
        return deleted

    # ==================== Scrape Run Operations ====================

    @retry_on_error()
    def create_scrape_run(self, session_id: str, cities_total: int) -> int:
        """Create a new scrape run."""
        result = self.client.table('us_scrape_runs').insert({
            'session_id': session_id,
            'cities_total': cities_total,
            'started_at': datetime.now().isoformat(),
        }).execute()

        return result.data[0]['id'] if result.data else None

    @retry_on_error()
    def update_scrape_run(
        self,
        run_id: int,
        cities_completed: Optional[int] = None,
        cities_failed: Optional[int] = None,
        hotels_found: Optional[int] = None,
        deals_found: Optional[int] = None,
        status: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """Update a scrape run."""
        updates = {}

        if cities_completed is not None:
            updates['cities_completed'] = cities_completed
        if cities_failed is not None:
            updates['cities_failed'] = cities_failed
        if hotels_found is not None:
            updates['hotels_found'] = hotels_found
        if deals_found is not None:
            updates['deals_found'] = deals_found
        if status is not None:
            updates['status'] = status
            if status in ('completed', 'failed'):
                updates['completed_at'] = datetime.now().isoformat()
        if error_message is not None:
            updates['error_message'] = error_message

        if updates:
            self.client.table('us_scrape_runs')\
                .update(updates)\
                .eq('id', run_id)\
                .execute()

    @retry_on_error()
    def get_latest_scrape_run(self) -> Optional[Dict[str, Any]]:
        """Get the most recent scrape run."""
        result = self.client.table('us_scrape_runs')\
            .select('*')\
            .order('started_at', desc=True)\
            .limit(1)\
            .execute()

        return result.data[0] if result.data else None

    # ==================== Statistics ====================

    @retry_on_error()
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}

        # Count cities
        result = self.client.table('us_hotel_cities')\
            .select('id', count='exact')\
            .eq('is_active', True)\
            .execute()
        stats['total_cities'] = result.count or 0

        result = self.client.table('us_hotel_cities')\
            .select('id', count='exact')\
            .not_.is_('agoda_place_id', 'null')\
            .execute()
        stats['cities_with_agoda_id'] = result.count or 0

        # Count hotels
        result = self.client.table('us_hotels')\
            .select('id', count='exact')\
            .execute()
        stats['total_hotels'] = result.count or 0

        # Count active deals
        today = datetime.now().date().isoformat()
        result = self.client.table('us_hotel_deals')\
            .select('id', count='exact')\
            .gte('check_in', today)\
            .execute()
        stats['active_deals'] = result.count or 0

        # Average and max yield
        result = self.client.table('us_hotel_deals')\
            .select('yield_ratio')\
            .gte('check_in', today)\
            .execute()

        if result.data:
            yields = [r['yield_ratio'] for r in result.data if r.get('yield_ratio')]
            stats['avg_yield'] = round(sum(yields) / len(yields), 2) if yields else 0
            stats['max_yield'] = round(max(yields), 2) if yields else 0
        else:
            stats['avg_yield'] = 0
            stats['max_yield'] = 0

        return stats


# Singleton instance
_supabase_db: Optional[SupabaseDatabase] = None


def get_supabase_database() -> SupabaseDatabase:
    """Get the Supabase database singleton."""
    global _supabase_db
    if _supabase_db is None:
        _supabase_db = SupabaseDatabase()
    return _supabase_db
