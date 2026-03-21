"""
SQLite database operations for AA Points Monitor.
Handles all CRUD operations, staleness detection, and expiration filtering.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging

from config.settings import get_settings

logger = logging.getLogger(__name__)


class Database:
    """SQLite database wrapper with connection pooling and helper methods."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection."""
        settings = get_settings()
        self.db_path = db_path or settings.database_path
        self._init_schema()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # SimplyMiles offers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simplymiles_offers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    merchant_name TEXT NOT NULL,
                    merchant_name_normalized TEXT NOT NULL,
                    offer_type TEXT NOT NULL,
                    miles_amount INTEGER NOT NULL,
                    lp_amount INTEGER NOT NULL,
                    min_spend REAL,
                    expires_at TEXT,
                    expiring_soon BOOLEAN DEFAULT FALSE,
                    scraped_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Portal rates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portal_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    merchant_name TEXT NOT NULL,
                    merchant_name_normalized TEXT NOT NULL,
                    miles_per_dollar REAL NOT NULL,
                    is_bonus_rate BOOLEAN DEFAULT FALSE,
                    category TEXT,
                    url TEXT,
                    scraped_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Hotel deals
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hotel_deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hotel_name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    state TEXT NOT NULL,
                    check_in TEXT NOT NULL,
                    check_out TEXT NOT NULL,
                    nightly_rate REAL NOT NULL,
                    base_miles INTEGER NOT NULL,
                    bonus_miles INTEGER DEFAULT 0,
                    total_miles INTEGER NOT NULL,
                    total_cost REAL NOT NULL,
                    yield_ratio REAL NOT NULL,
                    deal_score REAL NOT NULL,
                    url TEXT,
                    scraped_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Stacked opportunities
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stacked_opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    merchant_name TEXT NOT NULL,
                    portal_rate REAL NOT NULL,
                    portal_miles INTEGER NOT NULL,
                    simplymiles_type TEXT NOT NULL,
                    simplymiles_miles INTEGER NOT NULL,
                    simplymiles_min_spend REAL,
                    simplymiles_expires TEXT,
                    cc_miles INTEGER NOT NULL,
                    min_spend_required REAL NOT NULL,
                    total_miles INTEGER NOT NULL,
                    combined_yield REAL NOT NULL,
                    deal_score REAL NOT NULL,
                    computed_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Alert history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    deal_type TEXT NOT NULL,
                    deal_identifier TEXT NOT NULL,
                    deal_score REAL NOT NULL,
                    sent_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Scraper health tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraper_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scraper_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    items_scraped INTEGER DEFAULT 0,
                    run_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Hotel yield history for adaptive scanning
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hotel_yield_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    advance_days INTEGER NOT NULL,
                    avg_yield REAL NOT NULL,
                    max_yield REAL NOT NULL,
                    deal_count INTEGER NOT NULL,
                    scraped_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Hotel yield matrix - comprehensive permutation exploration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hotel_yield_matrix (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    advance_days INTEGER NOT NULL,

                    -- Aggregate stats
                    avg_yield REAL,
                    max_yield REAL,
                    min_yield REAL,
                    median_yield REAL,
                    deal_count INTEGER DEFAULT 0,

                    -- Star-tier breakdown
                    avg_yield_5star REAL,
                    avg_yield_4star REAL,
                    avg_yield_3star REAL,
                    avg_yield_2star REAL,
                    avg_yield_1star REAL,
                    count_5star INTEGER DEFAULT 0,
                    count_4star INTEGER DEFAULT 0,
                    count_3star INTEGER DEFAULT 0,
                    count_2star INTEGER DEFAULT 0,
                    count_1star INTEGER DEFAULT 0,

                    -- Best premium hotel (4-5 star)
                    top_premium_hotel TEXT,
                    top_premium_yield REAL,
                    top_premium_cost REAL,
                    top_premium_miles INTEGER,
                    top_premium_stars INTEGER,

                    -- Best budget hotel (1-3 star, only if exceptional)
                    top_budget_hotel TEXT,
                    top_budget_yield REAL,
                    top_budget_cost REAL,
                    top_budget_miles INTEGER,
                    top_budget_stars INTEGER,

                    -- Metadata
                    discovered_at TEXT,
                    last_verified_at TEXT,
                    verification_count INTEGER DEFAULT 1,
                    yield_stability REAL,

                    UNIQUE(city, day_of_week, duration, advance_days)
                )
            """)

            # Discovery progress tracking (for resume capability)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS discovery_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    city TEXT NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    duration INTEGER NOT NULL,
                    advance_days INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    hotels_found INTEGER DEFAULT 0,
                    error_message TEXT,
                    started_at TEXT,
                    completed_at TEXT
                )
            """)

            # Per-hotel yield baselines for deviation-based alerting
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hotel_yield_baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hotel_name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    star_rating INTEGER,
                    avg_yield REAL NOT NULL,
                    stddev_yield REAL DEFAULT 0,
                    min_yield REAL,
                    max_yield REAL,
                    observation_count INTEGER DEFAULT 1,
                    last_updated TEXT NOT NULL,
                    UNIQUE(hotel_name, city, day_of_week)
                )
            """)

            # Deal discoveries for "New This Week" tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deal_discoveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deal_type TEXT NOT NULL,
                    deal_identifier TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    times_seen INTEGER DEFAULT 1,
                    best_yield_seen REAL,
                    UNIQUE(deal_type, deal_identifier)
                )
            """)

            # Indexes - Core tables
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_simply_merchant ON simplymiles_offers(merchant_name_normalized)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_simply_scraped ON simplymiles_offers(scraped_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_simply_expires ON simplymiles_offers(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_portal_merchant ON portal_rates(merchant_name_normalized)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_portal_scraped ON portal_rates(scraped_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotels_city ON hotel_deals(city, state)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotels_checkin ON hotel_deals(check_in)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotels_score ON hotel_deals(deal_score DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stacked_score ON stacked_opportunities(deal_score DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stacked_computed ON stacked_opportunities(computed_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stacked_expires ON stacked_opportunities(simplymiles_expires)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_identifier ON alert_history(deal_identifier, sent_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scraper_health ON scraper_health(scraper_name, run_at)")

            # Indexes - Intelligence tables
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotel_yield_city ON hotel_yield_history(city, day_of_week, advance_days)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_yield_matrix_lookup ON hotel_yield_matrix(city, day_of_week, duration, advance_days)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_yield_matrix_yield ON hotel_yield_matrix(avg_yield DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_discovery_session ON discovery_progress(session_id, status)")

            # Indexes - Hotel baselines and discovery
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotel_baseline_lookup ON hotel_yield_baselines(hotel_name, city, day_of_week)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_discovery_type ON deal_discoveries(deal_type, first_seen_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_discovery_identifier ON deal_discoveries(deal_identifier)")

            logger.info(f"Database initialized at {self.db_path}")

    # ==================== SimplyMiles Operations ====================

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
    ) -> int:
        """Insert a SimplyMiles offer."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO simplymiles_offers
                (merchant_name, merchant_name_normalized, offer_type, miles_amount,
                 lp_amount, min_spend, expires_at, expiring_soon, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (merchant_name, merchant_name_normalized, offer_type, miles_amount,
                  lp_amount, min_spend, expires_at, expiring_soon, scraped_at))
            return cursor.lastrowid

    def get_active_simplymiles_offers(self) -> List[Dict[str, Any]]:
        """Get all non-expired SimplyMiles offers from the latest scrape."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get the latest scrape time
            cursor.execute("""
                SELECT MAX(scraped_at) as latest FROM simplymiles_offers
            """)
            latest = cursor.fetchone()
            if not latest or not latest['latest']:
                return []

            # Get offers from latest scrape that haven't expired
            now = datetime.now().isoformat()
            cursor.execute("""
                SELECT * FROM simplymiles_offers
                WHERE scraped_at = ?
                AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY miles_amount DESC
            """, (latest['latest'], now))

            return [dict(row) for row in cursor.fetchall()]

    def clear_simplymiles_offers(self):
        """Clear all SimplyMiles offers (before fresh scrape)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM simplymiles_offers")
            logger.info("Cleared SimplyMiles offers table")

    # ==================== Portal Operations ====================

    def insert_portal_rate(
        self,
        merchant_name: str,
        merchant_name_normalized: str,
        miles_per_dollar: float,
        is_bonus_rate: bool,
        category: Optional[str],
        url: Optional[str],
        scraped_at: str
    ) -> int:
        """Insert a portal rate."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO portal_rates
                (merchant_name, merchant_name_normalized, miles_per_dollar,
                 is_bonus_rate, category, url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (merchant_name, merchant_name_normalized, miles_per_dollar,
                  is_bonus_rate, category, url, scraped_at))
            return cursor.lastrowid

    def get_latest_portal_rates(self) -> List[Dict[str, Any]]:
        """Get portal rates from the latest scrape."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT MAX(scraped_at) as latest FROM portal_rates
            """)
            latest = cursor.fetchone()
            if not latest or not latest['latest']:
                return []

            cursor.execute("""
                SELECT * FROM portal_rates
                WHERE scraped_at = ?
                ORDER BY miles_per_dollar DESC
            """, (latest['latest'],))

            return [dict(row) for row in cursor.fetchall()]

    def clear_portal_rates(self):
        """Clear all portal rates (before fresh scrape)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM portal_rates")
            logger.info("Cleared portal rates table")

    # ==================== Hotel Operations ====================

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
    ) -> int:
        """Insert a hotel deal."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO hotel_deals
                (hotel_name, city, state, check_in, check_out, nightly_rate,
                 base_miles, bonus_miles, total_miles, total_cost, yield_ratio,
                 deal_score, url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (hotel_name, city, state, check_in, check_out, nightly_rate,
                  base_miles, bonus_miles, total_miles, total_cost, yield_ratio,
                  deal_score, url, scraped_at))
            return cursor.lastrowid

    def get_top_hotel_deals(
        self,
        city: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top hotel deals, optionally filtered by city."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if city:
                cursor.execute("""
                    SELECT * FROM hotel_deals
                    WHERE city = ? AND check_in > date('now')
                    ORDER BY deal_score DESC
                    LIMIT ?
                """, (city, limit))
            else:
                cursor.execute("""
                    SELECT * FROM hotel_deals
                    WHERE check_in > date('now')
                    ORDER BY deal_score DESC
                    LIMIT ?
                """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def clear_hotel_deals(self):
        """Clear all hotel deals (before fresh scrape)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hotel_deals")
            logger.info("Cleared hotel deals table")

    # ==================== Stacked Opportunities ====================

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
    ) -> int:
        """Insert a stacked opportunity."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO stacked_opportunities
                (merchant_name, portal_rate, portal_miles, simplymiles_type,
                 simplymiles_miles, simplymiles_min_spend, simplymiles_expires,
                 cc_miles, min_spend_required, total_miles, combined_yield,
                 deal_score, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (merchant_name, portal_rate, portal_miles, simplymiles_type,
                  simplymiles_miles, simplymiles_min_spend, simplymiles_expires,
                  cc_miles, min_spend_required, total_miles, combined_yield,
                  deal_score, computed_at))
            return cursor.lastrowid

    def get_top_stacked_opportunities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top stacked opportunities by deal score."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get from latest computation
            cursor.execute("""
                SELECT MAX(computed_at) as latest FROM stacked_opportunities
            """)
            latest = cursor.fetchone()
            if not latest or not latest['latest']:
                return []

            now = datetime.now().isoformat()
            cursor.execute("""
                SELECT * FROM stacked_opportunities
                WHERE computed_at = ?
                AND (simplymiles_expires IS NULL OR simplymiles_expires > ?)
                ORDER BY deal_score DESC
                LIMIT ?
            """, (latest['latest'], now, limit))

            return [dict(row) for row in cursor.fetchall()]

    def clear_stacked_opportunities(self):
        """Clear stacked opportunities (before recomputation)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stacked_opportunities")
            logger.info("Cleared stacked opportunities table")

    # ==================== Alert History ====================

    def insert_alert(
        self,
        alert_type: str,
        deal_type: str,
        deal_identifier: str,
        deal_score: float,
        sent_at: str
    ) -> int:
        """Record an alert in history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alert_history
                (alert_type, deal_type, deal_identifier, deal_score, sent_at)
                VALUES (?, ?, ?, ?, ?)
            """, (alert_type, deal_type, deal_identifier, deal_score, sent_at))
            return cursor.lastrowid

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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(hours=cooldown_hours)).isoformat()

            cursor.execute("""
                SELECT deal_score FROM alert_history
                WHERE deal_identifier = ? AND sent_at > ?
                ORDER BY sent_at DESC
                LIMIT 1
            """, (deal_identifier, cutoff))

            result = cursor.fetchone()
            if result:
                return True, result['deal_score']
            return False, None

    # ==================== Scraper Health ====================

    def record_scraper_run(
        self,
        scraper_name: str,
        status: str,
        error_message: Optional[str] = None,
        items_scraped: int = 0
    ):
        """Record a scraper run for health monitoring."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scraper_health
                (scraper_name, status, error_message, items_scraped, run_at)
                VALUES (?, ?, ?, ?, ?)
            """, (scraper_name, status, error_message, items_scraped,
                  datetime.now().isoformat()))

    def get_consecutive_failures(self, scraper_name: str) -> int:
        """Get count of consecutive failures for a scraper."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status FROM scraper_health
                WHERE scraper_name = ?
                ORDER BY run_at DESC
                LIMIT 10
            """, (scraper_name,))

            failures = 0
            for row in cursor.fetchall():
                if row['status'] == 'success':
                    break
                failures += 1

            return failures

    def get_last_successful_scrape(self, scraper_name: str) -> Optional[str]:
        """Get timestamp of last successful scrape."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT run_at FROM scraper_health
                WHERE scraper_name = ? AND status = 'success'
                ORDER BY run_at DESC
                LIMIT 1
            """, (scraper_name,))

            result = cursor.fetchone()
            return result['run_at'] if result else None

    # ==================== Staleness Detection ====================

    def get_latest_scrape_time(self, source: str) -> Optional[datetime]:
        """
        Get the latest scrape time for a data source.

        Args:
            source: 'simplymiles', 'portal', or 'hotels'

        Returns:
            datetime of latest scrape, or None if no data
        """
        table_map = {
            'simplymiles': 'simplymiles_offers',
            'portal': 'portal_rates',
            'hotels': 'hotel_deals'
        }

        if source not in table_map:
            raise ValueError(f"Unknown source: {source}")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT MAX(scraped_at) as latest FROM {table_map[source]}
            """)

            result = cursor.fetchone()
            if result and result['latest']:
                return datetime.fromisoformat(result['latest'])
            return None

    def is_data_stale(self, source: str) -> bool:
        """
        Check if data from a source is stale based on configured thresholds.

        Args:
            source: 'simplymiles', 'portal', or 'hotels'

        Returns:
            True if data is stale or missing
        """
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

    def record_hotel_yield(
        self,
        city: str,
        day_of_week: int,
        advance_days: int,
        avg_yield: float,
        max_yield: float,
        deal_count: int
    ):
        """
        Record historical hotel yield data for adaptive scanning.

        Args:
            city: City name
            day_of_week: 0-6 (Monday-Sunday)
            advance_days: Days in advance of booking
            avg_yield: Average yield from this scrape
            max_yield: Maximum yield from this scrape
            deal_count: Number of deals found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO hotel_yield_history
                (city, day_of_week, advance_days, avg_yield, max_yield, deal_count, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (city, day_of_week, advance_days, avg_yield, max_yield, deal_count,
                  datetime.now().isoformat()))

    def get_historical_yields(
        self,
        city: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical yield data for a city.

        Args:
            city: City name
            days_back: How many days of history to retrieve

        Returns:
            List of historical yield records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days_back)).isoformat()

            cursor.execute("""
                SELECT city, day_of_week, advance_days,
                       AVG(avg_yield) as avg_yield,
                       MAX(max_yield) as max_yield,
                       SUM(deal_count) as total_deals
                FROM hotel_yield_history
                WHERE city = ? AND scraped_at > ?
                GROUP BY city, day_of_week, advance_days
                ORDER BY avg_yield DESC
            """, (city, cutoff))

            return [dict(row) for row in cursor.fetchall()]

    def get_best_yield_slots(
        self,
        city: str,
        limit: int = 10,
        min_deals: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get the historically best-yielding (day_of_week, advance_days) combinations.

        Args:
            city: City name
            limit: Maximum number of slots to return
            min_deals: Minimum number of historical deals to consider slot valid

        Returns:
            List of (day_of_week, advance_days, avg_yield) tuples sorted by yield
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Look back 60 days for pattern detection
            cutoff = (datetime.now() - timedelta(days=60)).isoformat()

            cursor.execute("""
                SELECT day_of_week, advance_days,
                       AVG(avg_yield) as avg_yield,
                       MAX(max_yield) as max_yield,
                       SUM(deal_count) as total_deals
                FROM hotel_yield_history
                WHERE city = ? AND scraped_at > ?
                GROUP BY day_of_week, advance_days
                HAVING SUM(deal_count) >= ?
                ORDER BY AVG(avg_yield) DESC
                LIMIT ?
            """, (city, cutoff, min_deals, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_yield_prediction(
        self,
        city: str,
        day_of_week: int,
        advance_days: int
    ) -> Optional[float]:
        """
        Predict expected yield for a specific (city, day_of_week, advance_days) combo.

        Returns:
            Predicted average yield, or None if no historical data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=60)).isoformat()

            cursor.execute("""
                SELECT AVG(avg_yield) as predicted_yield
                FROM hotel_yield_history
                WHERE city = ? AND day_of_week = ? AND advance_days BETWEEN ? AND ?
                AND scraped_at > ?
            """, (city, day_of_week, advance_days - 7, advance_days + 7, cutoff))

            result = cursor.fetchone()
            return result['predicted_yield'] if result and result['predicted_yield'] else None

    # ==================== Hotel Yield Matrix ====================

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
        """
        Insert or update a yield matrix entry.

        Args:
            city: City name
            day_of_week: 0-6 (Monday-Sunday)
            duration: Number of nights (1, 2, 3)
            advance_days: Days in advance
            stats: Dict with avg_yield, max_yield, min_yield, median_yield, deal_count, star breakdowns
            top_premium: Best 4-5 star hotel dict
            top_budget: Best 1-3 star hotel dict (if exceptional)
        """
        now = datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if entry exists
            cursor.execute("""
                SELECT id, verification_count, avg_yield, yield_stability
                FROM hotel_yield_matrix
                WHERE city = ? AND day_of_week = ? AND duration = ? AND advance_days = ?
            """, (city, day_of_week, duration, advance_days))

            existing = cursor.fetchone()

            if existing:
                # Update existing entry
                old_yield = existing['avg_yield'] or 0
                new_yield = stats.get('avg_yield', 0)
                ver_count = existing['verification_count'] + 1

                # Calculate stability (exponential moving average of 1 - drift)
                if old_yield > 0 and new_yield > 0:
                    drift = abs(new_yield - old_yield) / old_yield
                    # Use stored stability or default to 1.0 for first verification
                    old_stability = existing['yield_stability'] if existing['yield_stability'] else 1.0
                    # EMA: 70% old stability, 30% new observation
                    stability = 0.7 * old_stability + 0.3 * (1.0 - min(drift, 1.0))
                else:
                    stability = existing['yield_stability']  # Keep existing if can't calculate

                cursor.execute("""
                    UPDATE hotel_yield_matrix SET
                        avg_yield = ?,
                        max_yield = ?,
                        min_yield = ?,
                        median_yield = ?,
                        deal_count = ?,
                        avg_yield_5star = ?,
                        avg_yield_4star = ?,
                        avg_yield_3star = ?,
                        avg_yield_2star = ?,
                        avg_yield_1star = ?,
                        count_5star = ?,
                        count_4star = ?,
                        count_3star = ?,
                        count_2star = ?,
                        count_1star = ?,
                        top_premium_hotel = ?,
                        top_premium_yield = ?,
                        top_premium_cost = ?,
                        top_premium_miles = ?,
                        top_premium_stars = ?,
                        top_budget_hotel = ?,
                        top_budget_yield = ?,
                        top_budget_cost = ?,
                        top_budget_miles = ?,
                        top_budget_stars = ?,
                        last_verified_at = ?,
                        verification_count = ?,
                        yield_stability = ?
                    WHERE id = ?
                """, (
                    stats.get('avg_yield'),
                    stats.get('max_yield'),
                    stats.get('min_yield'),
                    stats.get('median_yield'),
                    stats.get('deal_count', 0),
                    stats.get('avg_yield_5star'),
                    stats.get('avg_yield_4star'),
                    stats.get('avg_yield_3star'),
                    stats.get('avg_yield_2star'),
                    stats.get('avg_yield_1star'),
                    stats.get('count_5star', 0),
                    stats.get('count_4star', 0),
                    stats.get('count_3star', 0),
                    stats.get('count_2star', 0),
                    stats.get('count_1star', 0),
                    top_premium.get('hotel_name') if top_premium else None,
                    top_premium.get('yield_ratio') if top_premium else None,
                    top_premium.get('total_cost') if top_premium else None,
                    top_premium.get('total_miles') if top_premium else None,
                    top_premium.get('stars') if top_premium else None,
                    top_budget.get('hotel_name') if top_budget else None,
                    top_budget.get('yield_ratio') if top_budget else None,
                    top_budget.get('total_cost') if top_budget else None,
                    top_budget.get('total_miles') if top_budget else None,
                    top_budget.get('stars') if top_budget else None,
                    now,
                    ver_count,
                    stability,
                    existing['id']
                ))
            else:
                # Insert new entry
                cursor.execute("""
                    INSERT INTO hotel_yield_matrix (
                        city, day_of_week, duration, advance_days,
                        avg_yield, max_yield, min_yield, median_yield, deal_count,
                        avg_yield_5star, avg_yield_4star, avg_yield_3star, avg_yield_2star, avg_yield_1star,
                        count_5star, count_4star, count_3star, count_2star, count_1star,
                        top_premium_hotel, top_premium_yield, top_premium_cost, top_premium_miles, top_premium_stars,
                        top_budget_hotel, top_budget_yield, top_budget_cost, top_budget_miles, top_budget_stars,
                        discovered_at, last_verified_at, verification_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    city, day_of_week, duration, advance_days,
                    stats.get('avg_yield'),
                    stats.get('max_yield'),
                    stats.get('min_yield'),
                    stats.get('median_yield'),
                    stats.get('deal_count', 0),
                    stats.get('avg_yield_5star'),
                    stats.get('avg_yield_4star'),
                    stats.get('avg_yield_3star'),
                    stats.get('avg_yield_2star'),
                    stats.get('avg_yield_1star'),
                    stats.get('count_5star', 0),
                    stats.get('count_4star', 0),
                    stats.get('count_3star', 0),
                    stats.get('count_2star', 0),
                    stats.get('count_1star', 0),
                    top_premium.get('hotel_name') if top_premium else None,
                    top_premium.get('yield_ratio') if top_premium else None,
                    top_premium.get('total_cost') if top_premium else None,
                    top_premium.get('total_miles') if top_premium else None,
                    top_premium.get('stars') if top_premium else None,
                    top_budget.get('hotel_name') if top_budget else None,
                    top_budget.get('yield_ratio') if top_budget else None,
                    top_budget.get('total_cost') if top_budget else None,
                    top_budget.get('total_miles') if top_budget else None,
                    top_budget.get('stars') if top_budget else None,
                    now, now
                ))

    def get_matrix_entry(
        self,
        city: str,
        day_of_week: int,
        duration: int,
        advance_days: int
    ) -> Optional[Dict[str, Any]]:
        """Get a specific yield matrix entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM hotel_yield_matrix
                WHERE city = ? AND day_of_week = ? AND duration = ? AND advance_days = ?
            """, (city, day_of_week, duration, advance_days))

            result = cursor.fetchone()
            return dict(result) if result else None

    def get_top_matrix_entries(
        self,
        city: Optional[str] = None,
        min_stars: int = 4,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get top yield matrix entries.

        Args:
            city: Filter by city (optional)
            min_stars: Minimum star preference (uses premium yields for 4-5, overall for lower)
            limit: Maximum entries to return

        Returns:
            List of matrix entries sorted by yield
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if min_stars >= 4:
                # Prefer premium hotel yields
                yield_col = "COALESCE(top_premium_yield, avg_yield)"
            else:
                yield_col = "avg_yield"

            if city:
                cursor.execute(f"""
                    SELECT *, {yield_col} as sort_yield FROM hotel_yield_matrix
                    WHERE city = ? AND deal_count > 0
                    ORDER BY sort_yield DESC
                    LIMIT ?
                """, (city, limit))
            else:
                cursor.execute(f"""
                    SELECT *, {yield_col} as sort_yield FROM hotel_yield_matrix
                    WHERE deal_count > 0
                    ORDER BY sort_yield DESC
                    LIMIT ?
                """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_unexplored_combinations(
        self,
        cities: List[str],
        days_of_week: List[int],
        durations: List[int],
        advance_days_options: List[int]
    ) -> List[Tuple[str, int, int, int]]:
        """
        Get combinations not yet in the matrix.

        Returns:
            List of (city, day_of_week, duration, advance_days) tuples
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get all existing combinations
            cursor.execute("""
                SELECT city, day_of_week, duration, advance_days
                FROM hotel_yield_matrix
            """)

            existing = set()
            for row in cursor.fetchall():
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

    def get_stale_matrix_entries(
        self,
        days_old: int = 7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get matrix entries that haven't been verified recently."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days_old)).isoformat()

            cursor.execute("""
                SELECT * FROM hotel_yield_matrix
                WHERE last_verified_at < ? OR last_verified_at IS NULL
                ORDER BY last_verified_at ASC
                LIMIT ?
            """, (cutoff, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_matrix_stats(self) -> Dict[str, Any]:
        """Get overall statistics about the yield matrix."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as total_entries,
                    COUNT(CASE WHEN deal_count > 0 THEN 1 END) as entries_with_data,
                    AVG(avg_yield) as overall_avg_yield,
                    MAX(max_yield) as best_yield_ever,
                    AVG(verification_count) as avg_verifications,
                    MIN(last_verified_at) as oldest_verification
                FROM hotel_yield_matrix
            """)

            result = cursor.fetchone()
            return dict(result) if result else {}

    # ==================== Matrix-Aware Date Selection ====================

    def get_best_matrix_slots(
        self,
        city: str,
        duration: int = 1,
        limit: int = 20,
        min_stability: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get the best-yielding slots from the yield matrix for smart date selection.

        Uses the comprehensive yield matrix (1,176 combinations) instead of
        historical yield_history table.

        Args:
            city: City name
            duration: Stay duration in nights (1, 2, or 3)
            limit: Maximum number of slots to return
            min_stability: Minimum yield stability (0-1) to consider

        Returns:
            List of slots sorted by avg_yield, each with day_of_week, advance_days,
            avg_yield, max_yield, and yield_stability
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    day_of_week,
                    advance_days,
                    avg_yield,
                    max_yield,
                    deal_count,
                    yield_stability,
                    top_premium_hotel,
                    top_budget_hotel
                FROM hotel_yield_matrix
                WHERE city = ?
                    AND duration = ?
                    AND deal_count > 0
                    AND (yield_stability >= ? OR yield_stability IS NULL)
                ORDER BY avg_yield DESC
                LIMIT ?
            """, (city, duration, min_stability, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_matrix_yield_prediction(
        self,
        city: str,
        day_of_week: int,
        duration: int,
        advance_days: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get yield prediction from the matrix for a specific combination.

        Returns exact match if available, otherwise finds closest advance_days.

        Args:
            city: City name
            day_of_week: 0=Monday to 6=Sunday
            duration: Stay duration in nights
            advance_days: Days until check-in

        Returns:
            Dict with avg_yield, max_yield, stability, or None if no data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Try exact match first
            cursor.execute("""
                SELECT avg_yield, max_yield, deal_count, yield_stability
                FROM hotel_yield_matrix
                WHERE city = ? AND day_of_week = ? AND duration = ? AND advance_days = ?
            """, (city, day_of_week, duration, advance_days))

            result = cursor.fetchone()
            if result and result['avg_yield']:
                return dict(result)

            # Find closest advance_days match
            cursor.execute("""
                SELECT avg_yield, max_yield, deal_count, yield_stability,
                       ABS(advance_days - ?) as distance
                FROM hotel_yield_matrix
                WHERE city = ? AND day_of_week = ? AND duration = ?
                    AND deal_count > 0
                ORDER BY distance ASC
                LIMIT 1
            """, (advance_days, city, day_of_week, duration))

            result = cursor.fetchone()
            return dict(result) if result and result['avg_yield'] else None

    def get_priority_search_dates(
        self,
        city: str,
        duration: int = 1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get prioritized search dates for a city based on matrix data.

        Returns the best (day_of_week, advance_days) combinations to search
        for maximum expected yield.

        Args:
            city: City name
            duration: Stay duration
            limit: Max number of date slots

        Returns:
            List of {day_of_week, advance_days, expected_yield, confidence}
        """
        slots = self.get_best_matrix_slots(city, duration, limit * 2)

        # Score by yield and stability
        scored = []
        for slot in slots:
            stability = slot.get('yield_stability') or 0.8  # Default if unknown
            expected = slot['avg_yield'] * (0.5 + 0.5 * stability)  # Weight by stability
            scored.append({
                'day_of_week': slot['day_of_week'],
                'advance_days': slot['advance_days'],
                'expected_yield': expected,
                'avg_yield': slot['avg_yield'],
                'max_yield': slot['max_yield'],
                'confidence': stability
            })

        # Sort by expected yield
        scored.sort(key=lambda x: x['expected_yield'], reverse=True)
        return scored[:limit]

    # ==================== Discovery Progress ====================

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

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO discovery_progress
                (session_id, city, day_of_week, duration, advance_days, status, hotels_found, error_message, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, city, day_of_week, duration, advance_days, status, hotels_found, error_message, now, now))

    def get_discovery_progress(self, session_id: str) -> Dict[str, Any]:
        """Get progress stats for a discovery session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as total_attempts,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as errors,
                    SUM(hotels_found) as total_hotels_found,
                    MIN(started_at) as started,
                    MAX(completed_at) as last_update
                FROM discovery_progress
                WHERE session_id = ?
            """, (session_id,))

            result = cursor.fetchone()
            return dict(result) if result else {}

    def get_completed_combinations(self, session_id: str) -> set:
        """Get set of combinations already completed in this session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT city, day_of_week, duration, advance_days
                FROM discovery_progress
                WHERE session_id = ? AND status = 'success'
            """, (session_id,))

            return {(row['city'], row['day_of_week'], row['duration'], row['advance_days'])
                    for row in cursor.fetchall()}

    # ==================== Hotel Yield Baselines ====================

    def update_hotel_baseline(
        self,
        hotel_name: str,
        city: str,
        day_of_week: int,
        star_rating: int,
        yield_ratio: float
    ):
        """
        Update or create a hotel yield baseline using Welford's online algorithm.

        This maintains running average and standard deviation efficiently
        without storing all historical values.

        Args:
            hotel_name: Hotel name
            city: City name
            day_of_week: 0=Monday to 6=Sunday
            star_rating: Hotel star rating (1-5)
            yield_ratio: Current yield observation
        """
        now = datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check for existing baseline
            cursor.execute("""
                SELECT id, avg_yield, stddev_yield, min_yield, max_yield, observation_count
                FROM hotel_yield_baselines
                WHERE hotel_name = ? AND city = ? AND day_of_week = ?
            """, (hotel_name, city, day_of_week))

            existing = cursor.fetchone()

            if existing:
                # Update using Welford's algorithm for running mean and variance
                n = existing['observation_count'] + 1
                old_avg = existing['avg_yield']
                old_stddev = existing['stddev_yield'] or 0

                # Welford's online algorithm
                delta = yield_ratio - old_avg
                new_avg = old_avg + delta / n

                # For stddev, we track M2 (sum of squared differences)
                # stddev = sqrt(M2 / n), so M2 = stddev^2 * (n-1)
                if n > 2:
                    old_m2 = (old_stddev ** 2) * (n - 2) if old_stddev else 0
                    delta2 = yield_ratio - new_avg
                    new_m2 = old_m2 + delta * delta2
                    new_stddev = (new_m2 / (n - 1)) ** 0.5 if n > 1 else 0
                else:
                    new_stddev = abs(yield_ratio - new_avg) if n == 2 else 0

                new_min = min(existing['min_yield'] or yield_ratio, yield_ratio)
                new_max = max(existing['max_yield'] or yield_ratio, yield_ratio)

                cursor.execute("""
                    UPDATE hotel_yield_baselines SET
                        avg_yield = ?,
                        stddev_yield = ?,
                        min_yield = ?,
                        max_yield = ?,
                        observation_count = ?,
                        last_updated = ?
                    WHERE id = ?
                """, (new_avg, new_stddev, new_min, new_max, n, now, existing['id']))
            else:
                # Insert new baseline
                cursor.execute("""
                    INSERT INTO hotel_yield_baselines
                    (hotel_name, city, day_of_week, star_rating, avg_yield, stddev_yield,
                     min_yield, max_yield, observation_count, last_updated)
                    VALUES (?, ?, ?, ?, ?, 0, ?, ?, 1, ?)
                """, (hotel_name, city, day_of_week, star_rating, yield_ratio,
                      yield_ratio, yield_ratio, now))

    def get_hotel_baseline(
        self,
        hotel_name: str,
        city: str,
        day_of_week: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get the yield baseline for a specific hotel on a specific day of week.

        Returns:
            Dict with avg_yield, stddev_yield, min_yield, max_yield, observation_count
            or None if no baseline exists
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hotel_name, city, day_of_week, star_rating,
                       avg_yield, stddev_yield, min_yield, max_yield,
                       observation_count, last_updated
                FROM hotel_yield_baselines
                WHERE hotel_name = ? AND city = ? AND day_of_week = ?
            """, (hotel_name, city, day_of_week))

            result = cursor.fetchone()
            return dict(result) if result else None

    def get_city_star_tier_average(
        self,
        city: str,
        star_rating: int,
        day_of_week: Optional[int] = None
    ) -> Optional[float]:
        """
        Get the average yield for a star tier in a city (cold start fallback).

        Args:
            city: City name
            star_rating: Star rating to query
            day_of_week: Optional day filter (0-6)

        Returns:
            Average yield across all hotels in that tier, or None if no data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if day_of_week is not None:
                cursor.execute("""
                    SELECT AVG(avg_yield) as tier_avg
                    FROM hotel_yield_baselines
                    WHERE city = ? AND star_rating = ? AND day_of_week = ?
                    AND observation_count >= 2
                """, (city, star_rating, day_of_week))
            else:
                cursor.execute("""
                    SELECT AVG(avg_yield) as tier_avg
                    FROM hotel_yield_baselines
                    WHERE city = ? AND star_rating = ?
                    AND observation_count >= 2
                """, (city, star_rating))

            result = cursor.fetchone()
            return result['tier_avg'] if result and result['tier_avg'] else None

    # ==================== Deal Discoveries ====================

    def upsert_discovery(
        self,
        deal_type: str,
        deal_identifier: str,
        yield_value: Optional[float] = None
    ):
        """
        Record or update a deal discovery.

        On first observation: sets first_seen_at
        On subsequent: updates last_seen_at, times_seen, best_yield_seen

        Args:
            deal_type: 'stack', 'hotel', 'portal', or 'simplymiles'
            deal_identifier: Unique identifier (merchant_name or hotel_city)
            yield_value: Current yield (optional, tracks best)
        """
        now = datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Try to update existing
            cursor.execute("""
                UPDATE deal_discoveries SET
                    last_seen_at = ?,
                    times_seen = times_seen + 1,
                    best_yield_seen = MAX(COALESCE(best_yield_seen, 0), COALESCE(?, 0))
                WHERE deal_type = ? AND deal_identifier = ?
            """, (now, yield_value, deal_type, deal_identifier))

            if cursor.rowcount == 0:
                # Insert new discovery
                cursor.execute("""
                    INSERT INTO deal_discoveries
                    (deal_type, deal_identifier, first_seen_at, last_seen_at, times_seen, best_yield_seen)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (deal_type, deal_identifier, now, now, yield_value))

    def get_new_discoveries(
        self,
        days: int = 7,
        deal_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get deals first discovered within the last N days.

        Args:
            days: How many days back to look for first_seen_at
            deal_type: Optional filter by type

        Returns:
            List of discovery records with first_seen_at within window
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            if deal_type:
                cursor.execute("""
                    SELECT * FROM deal_discoveries
                    WHERE first_seen_at >= ? AND deal_type = ?
                    ORDER BY first_seen_at DESC
                """, (cutoff, deal_type))
            else:
                cursor.execute("""
                    SELECT * FROM deal_discoveries
                    WHERE first_seen_at >= ?
                    ORDER BY first_seen_at DESC
                """, (cutoff,))

            return [dict(row) for row in cursor.fetchall()]

    def is_new_discovery(
        self,
        deal_type: str,
        deal_identifier: str,
        days: int = 7
    ) -> bool:
        """
        Check if a deal was first discovered within the last N days.

        Args:
            deal_type: 'stack', 'hotel', 'portal', or 'simplymiles'
            deal_identifier: Unique identifier
            days: Window to consider "new"

        Returns:
            True if first_seen_at is within the window
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT first_seen_at FROM deal_discoveries
                WHERE deal_type = ? AND deal_identifier = ?
                AND first_seen_at >= ?
            """, (deal_type, deal_identifier, cutoff))

            return cursor.fetchone() is not None


# Singleton instance
_database: Database | None = None


def get_database():
    """
    Get the database singleton.

    Routes to SQLite or Supabase based on DB_MODE environment variable:
    - 'sqlite': Local SQLite database (default)
    - 'supabase': Cloud Supabase PostgreSQL
    """
    global _database
    if _database is None:
        settings = get_settings()
        if settings.db_mode == 'supabase':
            from core.supabase_db import SupabaseDatabase
            _database = SupabaseDatabase()
            logger.info("Using Supabase database")
        else:
            _database = Database()
            logger.info(f"Using SQLite database at {settings.database_path}")
    return _database

