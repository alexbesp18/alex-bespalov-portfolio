"""
SQLite database layer for US Hotel Scraper.

Provides async-compatible database operations with connection pooling.
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Singleton database instance
_database: Optional["Database"] = None


def get_database():
    """Get the singleton database instance.

    Returns SQLite or Supabase database based on DB_MODE setting.
    """
    global _database
    if _database is None:
        from config.settings import get_settings
        settings = get_settings()

        if settings.db_mode == "supabase":
            from .supabase_db import get_supabase_database
            _database = get_supabase_database()
        else:
            _database = Database(settings.db_path)
    return _database


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connection(self):
        """Get a database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize database schema."""
        with self.connection() as conn:
            cursor = conn.cursor()

            # Cities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    msa_name TEXT UNIQUE NOT NULL,
                    city_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    agoda_place_id TEXT,
                    population INTEGER,
                    latitude REAL,
                    longitude REAL,
                    is_active INTEGER DEFAULT 1,
                    discovered_at TEXT,
                    verified_at TEXT,
                    last_scraped_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Hotels table (deduplicated)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hotels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hotel_name TEXT NOT NULL,
                    city_id INTEGER NOT NULL REFERENCES cities(id),
                    neighborhood TEXT,
                    stars INTEGER DEFAULT 0,
                    rating REAL DEFAULT 0,
                    review_count INTEGER DEFAULT 0,
                    agoda_hotel_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(hotel_name, city_id)
                )
            """)

            # Hotel deals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hotel_deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hotel_id INTEGER NOT NULL REFERENCES hotels(id),
                    scrape_run_id INTEGER REFERENCES scrape_runs(id),
                    check_in TEXT NOT NULL,
                    check_out TEXT NOT NULL,
                    nights INTEGER NOT NULL,
                    adults INTEGER DEFAULT 2,
                    nightly_rate REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    base_miles INTEGER NOT NULL,
                    bonus_miles INTEGER DEFAULT 0,
                    total_miles INTEGER NOT NULL,
                    yield_ratio REAL NOT NULL,
                    deal_score REAL NOT NULL,
                    room_type TEXT,
                    url TEXT,
                    scraped_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Scrape runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    cities_total INTEGER DEFAULT 0,
                    cities_completed INTEGER DEFAULT 0,
                    cities_failed INTEGER DEFAULT 0,
                    hotels_found INTEGER DEFAULT 0,
                    deals_found INTEGER DEFAULT 0,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT
                )
            """)

            # Scrape progress table (for resumability)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scrape_run_id INTEGER NOT NULL REFERENCES scrape_runs(id),
                    city_id INTEGER NOT NULL REFERENCES cities(id),
                    date_searched TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    hotels_found INTEGER DEFAULT 0,
                    error_message TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    UNIQUE(scrape_run_id, city_id, date_searched)
                )
            """)

            # Create indexes for fast queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_deals_yield
                ON hotel_deals(yield_ratio DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_deals_hotel
                ON hotel_deals(hotel_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_deals_checkin
                ON hotel_deals(check_in)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_deals_score
                ON hotel_deals(deal_score DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_hotels_city
                ON hotels(city_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cities_active
                ON cities(is_active, agoda_place_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_progress_run
                ON scrape_progress(scrape_run_id, status)
            """)
            # Index for retention mode lookup (hotel_id, check_in, check_out)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_deals_hotel_dates
                ON hotel_deals(hotel_id, check_in, check_out)
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    # ============== City Operations ==============

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
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cities (msa_name, city_name, state, agoda_place_id,
                                   population, latitude, longitude, discovered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(msa_name) DO UPDATE SET
                    agoda_place_id = COALESCE(excluded.agoda_place_id, agoda_place_id),
                    population = COALESCE(excluded.population, population),
                    latitude = COALESCE(excluded.latitude, latitude),
                    longitude = COALESCE(excluded.longitude, longitude),
                    verified_at = CASE WHEN excluded.agoda_place_id IS NOT NULL
                                      THEN ? ELSE verified_at END
            """, (
                msa_name, city_name, state, agoda_place_id,
                population, latitude, longitude,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            cursor.execute("SELECT id FROM cities WHERE msa_name = ?", (msa_name,))
            return cursor.fetchone()[0]

    def get_active_cities(self) -> List[Dict[str, Any]]:
        """Get all active cities with Agoda place IDs."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, msa_name, city_name, state, agoda_place_id,
                       population, latitude, longitude
                FROM cities
                WHERE is_active = 1 AND agoda_place_id IS NOT NULL
                ORDER BY population DESC NULLS LAST
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_city_by_id(self, city_id: int) -> Optional[Dict[str, Any]]:
        """Get a city by ID."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cities WHERE id = ?", (city_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_city_by_name(self, city_name: str, state: str) -> Optional[Dict[str, Any]]:
        """Get a city by name and state."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cities WHERE city_name = ? AND state = ?",
                (city_name, state)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_cities_without_agoda_id(self) -> List[Dict[str, Any]]:
        """Get cities that need Agoda place ID discovery."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, msa_name, city_name, state
                FROM cities
                WHERE is_active = 1 AND agoda_place_id IS NULL
                ORDER BY population DESC NULLS LAST
            """)
            return [dict(row) for row in cursor.fetchall()]

    def update_city_last_scraped(self, city_id: int) -> None:
        """Mark a city as scraped now (checkpoint).

        BUG 3 FIX: Add missing checkpoint method for SQLite.
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cities SET last_scraped_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), city_id))
            logger.debug(f"Checkpointed city {city_id} as scraped")

    def get_cities_needing_scrape(self, max_age_hours: int = 24) -> List[Dict[str, Any]]:
        """Get cities that need to be scraped (not scraped within max_age_hours).

        BUG 3 FIX: Add missing checkpoint method for SQLite.

        Used for checkpoint/resume - returns cities where:
        - last_scraped_at is NULL (never scraped), OR
        - last_scraped_at is older than max_age_hours
        """
        cutoff = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()

        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, msa_name, city_name, state, agoda_place_id,
                       population, latitude, longitude
                FROM cities
                WHERE is_active = 1
                  AND agoda_place_id IS NOT NULL
                  AND (last_scraped_at IS NULL OR last_scraped_at < ?)
                ORDER BY population DESC NULLS LAST
            """, (cutoff,))
            return [dict(row) for row in cursor.fetchall()]

    # ============== Hotel Operations ==============

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
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO hotels (hotel_name, city_id, stars, rating,
                                   review_count, neighborhood, agoda_hotel_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(hotel_name, city_id) DO UPDATE SET
                    stars = excluded.stars,
                    rating = excluded.rating,
                    review_count = excluded.review_count,
                    neighborhood = COALESCE(excluded.neighborhood, neighborhood),
                    agoda_hotel_id = COALESCE(excluded.agoda_hotel_id, agoda_hotel_id)
            """, (hotel_name, city_id, stars, rating, review_count, neighborhood, agoda_hotel_id))

            cursor.execute(
                "SELECT id FROM hotels WHERE hotel_name = ? AND city_id = ?",
                (hotel_name, city_id)
            )
            return cursor.fetchone()[0]

    # ============== Deal Operations ==============

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

        Retention modes (set via DEAL_RETENTION_MODE env var):
        - 'all': Keep all deals (allows duplicates, shows price history)
        - 'best': Keep only best yield per (hotel_id, check_in, check_out)

        Returns:
            Deal ID if inserted/updated, None if skipped (existing deal is better or equal)
        """
        from config.settings import get_settings
        settings = get_settings()

        # BUG 4 FIX: Parse dates properly to handle timezone strings
        if isinstance(check_in, str):
            check_in_clean = check_in.replace('Z', '+00:00')
            try:
                check_in_dt = datetime.fromisoformat(check_in_clean)
            except ValueError:
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

        # Normalize date strings for storage/comparison (YYYY-MM-DD format)
        check_in_str = check_in_dt.strftime('%Y-%m-%d')
        check_out_str = check_out_dt.strftime('%Y-%m-%d')

        # Calculate nights from dates
        nights = (check_out_dt.date() - check_in_dt.date()).days if hasattr(check_out_dt, 'date') else (check_out_dt - check_in_dt).days

        if nightly_rate is None:
            nightly_rate = total_cost / nights if nights > 0 else total_cost
        if base_miles is None:
            base_miles = total_miles

        now = datetime.now().isoformat()

        with self.connection() as conn:
            cursor = conn.cursor()

            # Check retention mode
            if settings.deal_retention_mode == "best":
                # BUG 8 FIX: Compare strings directly instead of using date() function
                # This allows the index on (hotel_id, check_in, check_out) to be used
                cursor.execute("""
                    SELECT id, yield_ratio FROM hotel_deals
                    WHERE hotel_id = ? AND check_in = ? AND check_out = ?
                """, (hotel_id, check_in_str, check_out_str))
                existing = cursor.fetchone()

                if existing:
                    existing_id, existing_yield = existing

                    if yield_ratio > existing_yield:
                        # New is better - UPDATE existing record
                        cursor.execute("""
                            UPDATE hotel_deals SET
                                scrape_run_id = ?, nights = ?, adults = ?,
                                nightly_rate = ?, total_cost = ?, base_miles = ?,
                                bonus_miles = ?, total_miles = ?, yield_ratio = ?,
                                deal_score = ?, room_type = ?, url = ?, scraped_at = ?
                            WHERE id = ?
                        """, (
                            scrape_run_id, nights, adults, nightly_rate, total_cost,
                            base_miles, bonus_miles, total_miles, yield_ratio,
                            deal_score, room_type, url, now, existing_id
                        ))
                        logger.debug(f"Updated deal {existing_id}: {existing_yield:.1f} -> {yield_ratio:.1f} LP/$")
                        return existing_id
                    elif yield_ratio == existing_yield:
                        # BUG 6 FIX: Explicit logging for equal yield case
                        logger.debug(f"Skipped deal: equal yield {yield_ratio:.1f} LP/$, keeping existing id={existing_id}")
                        return None
                    else:
                        # Existing is better - SKIP
                        logger.debug(f"Skipped deal: existing {existing_yield:.1f} > new {yield_ratio:.1f} LP/$")
                        return None

            # Mode is 'all' OR no existing deal - INSERT new record
            cursor.execute("""
                INSERT INTO hotel_deals (
                    hotel_id, scrape_run_id, check_in, check_out, nights, adults,
                    nightly_rate, total_cost, base_miles, bonus_miles, total_miles,
                    yield_ratio, deal_score, room_type, url, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hotel_id, scrape_run_id, check_in_str, check_out_str, nights, adults,
                nightly_rate, total_cost, base_miles, bonus_miles, total_miles,
                yield_ratio, deal_score, room_type, url, now
            ))
            return cursor.lastrowid

    def get_top_deals(
        self,
        limit: int = 100,
        min_yield: float = 0,
        min_stars: int = 1,
        max_stars: int = 5,
        city_id: Optional[int] = None,
        check_in_start: Optional[str] = None,
        check_in_end: Optional[str] = None,
        order_by: str = "yield_ratio",
    ) -> List[Dict[str, Any]]:
        """Get top deals with filters."""
        with self.connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    d.id, d.check_in, d.check_out, d.nights,
                    d.nightly_rate, d.total_cost, d.total_miles,
                    d.yield_ratio, d.deal_score, d.url, d.scraped_at,
                    h.hotel_name, h.stars, h.rating, h.review_count, h.neighborhood,
                    c.city_name, c.state, c.msa_name
                FROM hotel_deals d
                JOIN hotels h ON d.hotel_id = h.id
                JOIN cities c ON h.city_id = c.id
                WHERE d.yield_ratio >= ?
                  AND h.stars >= ?
                  AND h.stars <= ?
                  AND d.check_in >= date('now')
            """
            params = [min_yield, min_stars, max_stars]

            if city_id:
                query += " AND c.id = ?"
                params.append(city_id)

            if check_in_start:
                query += " AND d.check_in >= ?"
                params.append(check_in_start)

            if check_in_end:
                query += " AND d.check_in <= ?"
                params.append(check_in_end)

            # Order by
            order_column = {
                "yield_ratio": "d.yield_ratio DESC",
                "deal_score": "d.deal_score DESC",
                "total_cost": "d.total_cost ASC",
                "stars": "h.stars DESC",
                "check_in": "d.check_in ASC",
            }.get(order_by, "d.yield_ratio DESC")

            query += f" ORDER BY {order_column} LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_deals_by_city(
        self,
        city_id: int,
        limit: int = 100,
        min_yield: float = 0,
    ) -> List[Dict[str, Any]]:
        """Get deals for a specific city."""
        return self.get_top_deals(
            limit=limit,
            min_yield=min_yield,
            city_id=city_id,
        )

    def clear_old_deals(self, days_old: int = 7):
        """Delete deals with check_in dates in the past."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM hotel_deals
                WHERE check_in < date('now', ?)
            """, (f'-{days_old} days',))
            deleted = cursor.rowcount
            logger.info(f"Deleted {deleted} old deals")
            return deleted

    # ============== Scrape Run Operations ==============

    def create_scrape_run(self, session_id: str, cities_total: int) -> int:
        """Create a new scrape run."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scrape_runs (session_id, cities_total, started_at)
                VALUES (?, ?, ?)
            """, (session_id, cities_total, datetime.now().isoformat()))
            return cursor.lastrowid

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
        updates = []
        params = []

        if cities_completed is not None:
            updates.append("cities_completed = ?")
            params.append(cities_completed)
        if cities_failed is not None:
            updates.append("cities_failed = ?")
            params.append(cities_failed)
        if hotels_found is not None:
            updates.append("hotels_found = ?")
            params.append(hotels_found)
        if deals_found is not None:
            updates.append("deals_found = ?")
            params.append(deals_found)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
            if status in ("completed", "failed"):
                updates.append("completed_at = ?")
                params.append(datetime.now().isoformat())
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        if updates:
            params.append(run_id)
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE scrape_runs SET {', '.join(updates)} WHERE id = ?",
                    params
                )

    def get_latest_scrape_run(self) -> Optional[Dict[str, Any]]:
        """Get the most recent scrape run."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM scrape_runs
                ORDER BY started_at DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None

    # ============== Progress Tracking ==============

    def mark_progress(
        self,
        scrape_run_id: int,
        city_id: int,
        date_searched: str,
        status: str,
        hotels_found: int = 0,
        error_message: Optional[str] = None,
    ):
        """Mark progress for a city/date combination."""
        with self.connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO scrape_progress
                    (scrape_run_id, city_id, date_searched, status, hotels_found,
                     error_message, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(scrape_run_id, city_id, date_searched) DO UPDATE SET
                    status = excluded.status,
                    hotels_found = excluded.hotels_found,
                    error_message = excluded.error_message,
                    completed_at = excluded.completed_at
            """, (scrape_run_id, city_id, date_searched, status, hotels_found,
                  error_message, now, now if status != 'pending' else None))

    def get_pending_searches(
        self,
        scrape_run_id: int
    ) -> List[Tuple[int, str]]:
        """Get pending city/date combinations for resume."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT city_id, date_searched
                FROM scrape_progress
                WHERE scrape_run_id = ? AND status = 'pending'
            """, (scrape_run_id,))
            return [(row[0], row[1]) for row in cursor.fetchall()]

    # ============== Statistics ==============

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.connection() as conn:
            cursor = conn.cursor()

            stats = {}

            cursor.execute("SELECT COUNT(*) FROM cities WHERE is_active = 1")
            stats['total_cities'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cities WHERE agoda_place_id IS NOT NULL")
            stats['cities_with_agoda_id'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM hotels")
            stats['total_hotels'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM hotel_deals WHERE check_in >= date('now')")
            stats['active_deals'] = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(yield_ratio) FROM hotel_deals WHERE check_in >= date('now')")
            avg = cursor.fetchone()[0]
            stats['avg_yield'] = round(avg, 2) if avg else 0

            cursor.execute("SELECT MAX(yield_ratio) FROM hotel_deals WHERE check_in >= date('now')")
            max_yield = cursor.fetchone()[0]
            stats['max_yield'] = round(max_yield, 2) if max_yield else 0

            return stats
