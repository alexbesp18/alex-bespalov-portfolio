"""Core module for AA Points Monitor."""

from .database import Database, get_database
from .normalizer import normalize_merchant, find_best_match
from .scorer import calculate_stack_yield, calculate_hotel_yield, calculate_deal_score

__all__ = [
    "Database",
    "get_database",
    "normalize_merchant",
    "find_best_match",
    "calculate_stack_yield",
    "calculate_hotel_yield",
    "calculate_deal_score",
]

