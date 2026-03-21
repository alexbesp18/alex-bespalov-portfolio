"""
Custom exception hierarchy for US Hotel Scraper.

Provides structured error handling across the application.
"""


class HotelScraperError(Exception):
    """Base exception for all hotel scraper errors."""
    pass


# ============== HTTP Errors ==============

class HttpClientError(HotelScraperError):
    """Base exception for HTTP client errors."""
    pass


class RetryableError(HttpClientError):
    """Error that can be retried."""
    pass


class RateLimitError(RetryableError):
    """Rate limit exceeded (429)."""
    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        msg = f"Rate limited. Retry after: {retry_after}s" if retry_after else "Rate limited"
        super().__init__(msg)


class AuthenticationError(HttpClientError):
    """Authentication failed (401/403)."""
    pass


class ServerError(RetryableError):
    """Server error (5xx)."""
    pass


class TimeoutError(RetryableError):
    """Request timed out."""
    pass


# ============== Database Errors ==============

class DatabaseError(HotelScraperError):
    """Base exception for database errors."""
    pass


class DataIntegrityError(DatabaseError):
    """Data integrity constraint violated."""
    pass


# ============== Scraper Errors ==============

class ScraperError(HotelScraperError):
    """Base exception for scraper-related errors."""
    pass


class CityNotFoundError(ScraperError):
    """City not found in places API."""
    def __init__(self, city_name: str):
        self.city_name = city_name
        super().__init__(f"City not found: {city_name}")


class NoResultsError(ScraperError):
    """No results returned from search."""
    def __init__(self, city_name: str, date: str = None):
        self.city_name = city_name
        self.date = date
        msg = f"No results for {city_name}"
        if date:
            msg += f" on {date}"
        super().__init__(msg)
