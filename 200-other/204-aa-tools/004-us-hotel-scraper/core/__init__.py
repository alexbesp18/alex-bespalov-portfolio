"""Core module with shared utilities."""
from .database import Database, get_database
from .http_client import fetch_json, create_client
from .exceptions import (
    HotelScraperError,
    HttpClientError,
    RetryableError,
    RateLimitError,
    DatabaseError,
)

__all__ = [
    "Database",
    "get_database",
    "fetch_json",
    "create_client",
    "HotelScraperError",
    "HttpClientError",
    "RetryableError",
    "RateLimitError",
    "DatabaseError",
]
