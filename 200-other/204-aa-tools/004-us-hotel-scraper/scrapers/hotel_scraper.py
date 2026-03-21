"""
Async hotel scraper for US-wide hotel deals.

Scrapes hotels across all US MSAs with parallel processing.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config.settings import get_settings
from core.database import get_database
from core.http_client import create_client, random_delay
from core.hotels_api import search_hotels
from core.scorer import calculate_deal_score

logger = logging.getLogger(__name__)

# Only store deals meeting this threshold (enables massive scale scanning)
MIN_YIELD_TO_STORE = 25.0

console = Console()


def generate_search_dates(days_ahead: int = 30) -> List[Tuple[datetime, datetime]]:
    """
    Generate check-in/check-out date pairs for searching.

    Args:
        days_ahead: How many days ahead to search

    Returns:
        List of (check_in, check_out) datetime tuples
    """
    dates = []
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for day_offset in range(1, days_ahead + 1):
        check_in = today + timedelta(days=day_offset)

        # 1-night stays (daily)
        check_out = check_in + timedelta(days=1)
        dates.append((check_in, check_out))

        # 2-night stays (weekends: Fri-Sun, Sat-Mon)
        if check_in.weekday() in (4, 5):  # Friday or Saturday
            check_out = check_in + timedelta(days=2)
            dates.append((check_in, check_out))

    # Remove duplicates and sort
    unique_dates = list(set(dates))
    unique_dates.sort(key=lambda x: x[0])

    return unique_dates


class HotelScraper:
    """Async hotel scraper with progress tracking."""

    def __init__(
        self,
        max_concurrent: int = 10,
        days_ahead: int = 30,
        min_delay: float = 0.5,
        max_delay: float = 1.5,
    ):
        self.max_concurrent = max_concurrent
        self.days_ahead = days_ahead
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.db = get_database()
        self.session_id = str(uuid.uuid4())[:8]

    async def scrape_city(
        self,
        client,
        city: Dict[str, Any],
        dates: List[Tuple[datetime, datetime]],
        progress: Optional[Progress] = None,
        task_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape hotels for a single city across all dates.

        Args:
            client: HTTP client
            city: City dict from database
            dates: List of (check_in, check_out) tuples
            progress: Optional Rich progress bar
            task_id: Optional progress task ID

        Returns:
            List of hotel deals
        """
        city_name = city['city_name']
        state = city['state']
        place_id = city['agoda_place_id']
        city_id = city['id']

        all_hotels = []
        adults = 2  # Analysis showed no yield difference between 1 and 2 adults

        # Search all dates
        for check_in, check_out in dates:
            try:
                await random_delay(self.min_delay, self.max_delay)

                hotels = await search_hotels(
                    client, place_id, city_name, state, check_in, check_out, adults
                )

                # Process and score each hotel
                for hotel in hotels:
                    hotel['city_id'] = city_id
                    hotel['adults'] = adults
                    hotel['deal_score'] = calculate_deal_score(
                        hotel['yield_ratio'],
                        hotel['total_cost'],
                        hotel['stars'],
                    )
                    all_hotels.append(hotel)

            except Exception as e:
                logger.debug(f"Error searching {city_name} for {check_in.date()}: {e}")

            if progress and task_id:
                progress.update(task_id, advance=1)

        # Deduplicate by hotel name + date + adults (keep best yield)
        seen = {}
        for hotel in all_hotels:
            key = f"{hotel['hotel_name']}_{hotel['check_in']}_{hotel['adults']}"
            if key not in seen or hotel['yield_ratio'] > seen[key]['yield_ratio']:
                seen[key] = hotel

        unique_hotels = list(seen.values())

        return unique_hotels

    async def scrape_all(
        self,
        city_limit: Optional[int] = None,
        show_progress: bool = True,
        custom_dates: Optional[List[Tuple[datetime, datetime]]] = None,
        force_all: bool = False,
        max_age_hours: int = 8,
    ) -> Dict[str, Any]:
        """
        Scrape hotels for all active cities with checkpoint support.

        Args:
            city_limit: Optional limit on number of cities
            show_progress: Whether to show progress bar
            custom_dates: Optional custom date list (overrides generate_search_dates)
            force_all: If True, scrape all cities ignoring last_scraped_at
            max_age_hours: Re-scrape cities older than this (default 8h for 3x daily runs)

        Returns:
            Dict with scrape statistics
        """
        # Get cities - either all or only those needing scrape
        if force_all:
            cities = self.db.get_active_cities()
            logger.info("Force mode: scraping all cities")
        else:
            cities = self.db.get_cities_needing_scrape(max_age_hours=max_age_hours)
            logger.info(f"Resume mode: {len(cities)} cities need scraping (>{max_age_hours}h old or never scraped)")

        if city_limit:
            cities = cities[:city_limit]

        if not cities:
            logger.warning("No active cities with Agoda place IDs found")
            return {'status': 'error', 'message': 'No cities to scrape'}

        # Generate or use custom search dates
        if custom_dates:
            dates = custom_dates
        else:
            dates = generate_search_dates(self.days_ahead)

        logger.info(f"Scraping {len(cities)} cities, {len(dates)} dates each (1 & 2 adults)")

        # Create scrape run
        run_id = self.db.create_scrape_run(self.session_id, len(cities))

        results = {
            'status': 'running',
            'session_id': self.session_id,
            'run_id': run_id,
            'cities_total': len(cities),
            'cities_completed': 0,
            'cities_failed': 0,
            'hotels_found': 0,
            'deals_found': 0,
            'started_at': datetime.now().isoformat(),
        }

        semaphore = asyncio.Semaphore(self.max_concurrent)
        all_deals = []

        async def scrape_with_limit(city, progress=None, task_id=None):
            async with semaphore:
                try:
                    hotels = await self.scrape_city(client, city, dates, progress, task_id)
                    return city, hotels, None
                except Exception as e:
                    return city, [], str(e)

        async with create_client() as client:
            if show_progress:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console,
                ) as progress:
                    main_task = progress.add_task(
                        f"[cyan]Scraping {len(cities)} cities...",
                        total=len(cities)
                    )

                    tasks = [
                        scrape_with_limit(city, progress, main_task)
                        for city in cities
                    ]
                    outcomes = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                tasks = [scrape_with_limit(city) for city in cities]
                outcomes = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and checkpoint each city
        for outcome in outcomes:
            if isinstance(outcome, Exception):
                results['cities_failed'] += 1
                logger.error(f"Scrape error: {outcome}")
            else:
                city, hotels, error = outcome
                if error:
                    results['cities_failed'] += 1
                    logger.warning(f"Failed {city['city_name']}: {error}")
                else:
                    results['cities_completed'] += 1
                    results['hotels_found'] += len(set(h['hotel_name'] for h in hotels))
                    results['deals_found'] += len(hotels)
                    all_deals.extend(hotels)

                    # Checkpoint: mark city as scraped
                    try:
                        self.db.update_city_last_scraped(city['id'])
                    except Exception as e:
                        logger.warning(f"Failed to checkpoint {city['city_name']}: {e}")

        # Filter deals by yield threshold before storing
        # This enables scanning everything while keeping database small
        worthy_deals = [d for d in all_deals if d['yield_ratio'] >= MIN_YIELD_TO_STORE]
        logger.info(f"Found {len(all_deals)} total deals, {len(worthy_deals)} meet {MIN_YIELD_TO_STORE}+ LP/$ threshold")

        # Store only worthy deals in database
        stored = 0
        for deal in worthy_deals:
            try:
                # Upsert hotel first
                hotel_id = self.db.upsert_hotel(
                    hotel_name=deal['hotel_name'],
                    city_id=deal['city_id'],
                    stars=deal['stars'],
                    rating=deal['rating'],
                    review_count=deal['review_count'],
                    neighborhood=deal.get('neighborhood'),
                    agoda_hotel_id=deal.get('agoda_hotel_id'),
                )

                # Insert deal
                # BUG 2 FIX: Check return value - None means deal was skipped (existing is better)
                deal_id = self.db.insert_deal(
                    hotel_id=hotel_id,
                    check_in=deal['check_in'],
                    check_out=deal['check_out'],
                    total_cost=deal['total_cost'],
                    total_miles=deal['total_miles'],
                    yield_ratio=deal['yield_ratio'],
                    deal_score=deal['deal_score'],
                    scrape_run_id=run_id,
                    nightly_rate=deal['nightly_rate'],
                    base_miles=deal['base_miles'],
                    bonus_miles=deal['bonus_miles'],
                    url=deal.get('url'),
                    adults=deal.get('adults', 2),
                )
                if deal_id is not None:
                    stored += 1

            except Exception as e:
                logger.debug(f"Error storing deal: {e}")

        # Update scrape run
        results['status'] = 'completed'
        results['completed_at'] = datetime.now().isoformat()
        results['deals_stored'] = stored

        self.db.update_scrape_run(
            run_id,
            cities_completed=results['cities_completed'],
            cities_failed=results['cities_failed'],
            hotels_found=results['hotels_found'],
            deals_found=stored,
            status='completed',
        )

        logger.info(
            f"Scrape complete: {results['cities_completed']}/{results['cities_total']} cities, "
            f"{stored} deals stored"
        )

        return results


async def scrape_all_cities(
    city_limit: Optional[int] = None,
    max_concurrent: int = 10,
    days_ahead: int = 30,
    show_progress: bool = True,
    custom_dates: Optional[List[Tuple[datetime, datetime]]] = None,
    force_all: bool = False,
    max_age_hours: int = 8,
) -> Dict[str, Any]:
    """
    Convenience function to scrape all cities with checkpoint support.

    Args:
        city_limit: Optional limit on number of cities
        max_concurrent: Maximum parallel city scrapes
        days_ahead: Days ahead to search
        show_progress: Whether to show progress bar
        custom_dates: Optional custom date list (overrides days_ahead)
        force_all: If True, scrape all cities ignoring last_scraped_at
        max_age_hours: Re-scrape cities older than this (default 8h for 3x daily runs)

    Returns:
        Dict with scrape statistics
    """
    settings = get_settings()

    scraper = HotelScraper(
        max_concurrent=max_concurrent or settings.max_concurrent_cities,
        days_ahead=days_ahead or settings.days_ahead,
        min_delay=settings.min_delay,
        max_delay=settings.max_delay,
    )

    return await scraper.scrape_all(
        city_limit=city_limit,
        show_progress=show_progress,
        custom_dates=custom_dates,
        force_all=force_all,
        max_age_hours=max_age_hours,
    )
