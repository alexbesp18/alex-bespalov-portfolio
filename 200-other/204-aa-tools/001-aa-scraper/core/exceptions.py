"""
Custom exception hierarchy for AA Points Monitor.

Provides structured error handling across the application.
"""


class AAMonitorError(Exception):
    """Base exception for all AA Monitor errors."""
    pass


# ============== Scraper Errors ==============

class ScraperError(AAMonitorError):
    """Base exception for scraper-related errors."""
    pass


class SessionExpiredError(ScraperError):
    """Browser session or cookies have expired."""
    def __init__(self, scraper_name: str, message: str = "Session expired"):
        self.scraper_name = scraper_name
        super().__init__(f"{scraper_name}: {message}")


class ParseError(ScraperError):
    """Failed to parse data from source."""
    def __init__(self, source: str, reason: str):
        self.source = source
        self.reason = reason
        super().__init__(f"Parse error in {source}: {reason}")


class NoDataError(ScraperError):
    """No data returned from source."""
    def __init__(self, source: str):
        self.source = source
        super().__init__(f"No data returned from {source}")


# ============== HTTP Errors ==============

class HttpClientError(AAMonitorError):
    """Base exception for HTTP client errors."""
    pass


class RetryableError(HttpClientError):
    """Error that can be retried."""
    pass


class RateLimitError(RetryableError):
    """Rate limit exceeded (429)."""
    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after: {retry_after}s")


class AuthenticationError(HttpClientError):
    """Authentication failed (401/403)."""
    pass


class ServerError(RetryableError):
    """Server error (5xx)."""
    pass


# ============== Database Errors ==============

class DatabaseError(AAMonitorError):
    """Base exception for database errors."""
    pass


class DataIntegrityError(DatabaseError):
    """Data integrity constraint violated."""
    pass


class StaleDataError(DatabaseError):
    """Data is too old to be reliable."""
    def __init__(self, source: str, age_hours: float):
        self.source = source
        self.age_hours = age_hours
        super().__init__(f"{source} data is stale ({age_hours:.1f}h old)")


# ============== Alert Errors ==============

class AlertError(AAMonitorError):
    """Base exception for alert-related errors."""
    pass


class EmailDeliveryError(AlertError):
    """Failed to send email alert."""
    pass


class PushNotificationError(AlertError):
    """Failed to send push notification."""
    pass


# ============== Configuration Errors ==============

class ConfigurationError(AAMonitorError):
    """Configuration is missing or invalid."""
    pass


class MissingEnvVarError(ConfigurationError):
    """Required environment variable is missing."""
    def __init__(self, var_name: str):
        self.var_name = var_name
        super().__init__(f"Missing required environment variable: {var_name}")
