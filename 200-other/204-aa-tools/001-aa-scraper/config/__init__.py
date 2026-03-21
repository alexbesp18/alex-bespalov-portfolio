"""Configuration module for AA Points Monitor."""

from .settings import Settings, get_settings
from .cities import PRIORITY_CITIES, get_search_dates

__all__ = ["Settings", "get_settings", "PRIORITY_CITIES", "get_search_dates"]

