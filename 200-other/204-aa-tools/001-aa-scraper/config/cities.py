"""
Hotel city configurations for AA Points Monitor.
Defines priority cities and date range generation.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple


@dataclass
class City:
    """City configuration for hotel searches."""

    name: str
    state: str
    airport_code: str
    priority: int  # 1 = highest priority
    latitude: float = 0.0
    longitude: float = 0.0
    agoda_place_id: str = ""  # Format: "AGODA_CITY|XXXX"
    is_local: bool = False  # Austin gets special scoring bonus

    @property
    def display_name(self) -> str:
        return f"{self.name}, {self.state}"

    @property
    def search_query(self) -> str:
        return f"{self.name} ({self.state}), United States"


# Priority cities for hotel searches
# Coordinates and Agoda place IDs for AAdvantage Hotels search
PRIORITY_CITIES: List[City] = [
    City(name="Austin", state="TX", airport_code="AUS", priority=1,
         latitude=30.267153, longitude=-97.743061, agoda_place_id="AGODA_CITY|4542", is_local=True),
    City(name="Dallas", state="TX", airport_code="DFW", priority=2,
         latitude=32.783056, longitude=-96.806667, agoda_place_id="AGODA_CITY|8683"),
    City(name="Houston", state="TX", airport_code="IAH", priority=2,
         latitude=29.763284, longitude=-95.363271, agoda_place_id="AGODA_CITY|1178"),
    City(name="Las Vegas", state="NV", airport_code="LAS", priority=2,
         latitude=36.163934, longitude=-115.146332, agoda_place_id="AGODA_CITY|17072"),
    City(name="New York", state="NY", airport_code="JFK", priority=3,
         latitude=40.725548, longitude=-73.866577, agoda_place_id="AGODA_CITY|318"),
    City(name="Boston", state="MA", airport_code="BOS", priority=3,
         latitude=42.361588, longitude=-71.054764, agoda_place_id="AGODA_CITY|9254"),
    City(name="San Francisco", state="CA", airport_code="SFO", priority=3,
         latitude=37.770817, longitude=-122.418118, agoda_place_id="AGODA_CITY|13801"),
    City(name="Los Angeles", state="CA", airport_code="LAX", priority=3,
         latitude=34.060502, longitude=-118.239733, agoda_place_id="AGODA_CITY|12772"),
]


def get_search_dates(
    days_ahead: int = 90,
    weekend_heavy: bool = True
) -> List[Tuple[datetime, datetime]]:
    """
    Generate check-in/check-out date pairs for hotel searches.

    Args:
        days_ahead: How many days into the future to search
        weekend_heavy: If True, prioritize weekends

    Returns:
        List of (check_in, check_out) datetime tuples
    """
    dates = []
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today + timedelta(days=days_ahead)

    current = today + timedelta(days=1)  # Start from tomorrow

    while current < end_date:
        weekday = current.weekday()

        if weekend_heavy:
            # Friday-Saturday stays (weekend)
            if weekday == 4:  # Friday
                check_in = current
                check_out = current + timedelta(days=2)  # Sunday checkout
                dates.append((check_in, check_out))

            # Saturday-Sunday stays
            elif weekday == 5:  # Saturday
                check_in = current
                check_out = current + timedelta(days=1)
                dates.append((check_in, check_out))

            # Sample some weekdays (every 2 weeks)
            elif weekday == 2 and current.day <= 14:  # Tuesday, first half of month
                check_in = current
                check_out = current + timedelta(days=2)  # Thursday checkout
                dates.append((check_in, check_out))
        else:
            # Just sample weekly
            if weekday == 4:  # Every Friday
                check_in = current
                check_out = current + timedelta(days=2)
                dates.append((check_in, check_out))

        current += timedelta(days=1)

    return dates


def get_cities_by_priority(max_priority: int = 3) -> List[City]:
    """Get cities filtered by priority level."""
    return [c for c in PRIORITY_CITIES if c.priority <= max_priority]


def get_local_city() -> City:
    """Get the local city (Austin)."""
    return next(c for c in PRIORITY_CITIES if c.is_local)

