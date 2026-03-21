"""
Merchant name normalization and fuzzy matching for AA Points Monitor.
Handles matching between SimplyMiles and Portal merchant names.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process

from config.settings import get_settings

logger = logging.getLogger(__name__)


def normalize_merchant(name: str) -> str:
    """
    Normalize a merchant name for consistent matching.

    Args:
        name: Raw merchant name from scraper

    Returns:
        Normalized lowercase name with common variations removed
    """
    if not name:
        return ""

    # Lowercase and strip whitespace
    name = name.lower().strip()

    # Remove common suffixes
    suffixes = [
        '.com', '.net', '.org', '.co', '.io',
        ' inc', ' inc.', ' llc', ' llc.', ' corp', ' corp.',
        ' co', ' co.', ' company', ' corporation',
        ' stores', ' store', ' shop', ' online',
        ' us', ' usa', ' america',
    ]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]

    # Remove special characters but keep spaces
    name = re.sub(r'[^a-z0-9\s\-]', '', name)

    # Normalize hyphens and spaces
    name = re.sub(r'[\s\-]+', ' ', name)

    # Collapse multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()

    # Apply known aliases
    settings = get_settings()
    if name in settings.matching.aliases:
        name = settings.matching.aliases[name]

    return name


def find_best_match(
    name: str,
    candidates: List[str],
    threshold: Optional[int] = None
) -> Optional[Tuple[str, int]]:
    """
    Find the best fuzzy match for a merchant name.

    Args:
        name: Normalized name to match
        candidates: List of normalized candidate names
        threshold: Minimum similarity score (0-100), defaults to config

    Returns:
        Tuple of (matched_name, score) or None if no match above threshold
    """
    if not name or not candidates:
        return None

    settings = get_settings()
    threshold = threshold or settings.matching.fuzzy_threshold

    # Use rapidfuzz for fast fuzzy matching
    result = process.extractOne(
        name,
        candidates,
        scorer=fuzz.token_sort_ratio,  # Handles word order differences
        score_cutoff=threshold
    )

    if result:
        matched_name, score, _ = result
        logger.debug(f"Matched '{name}' -> '{matched_name}' (score: {score})")
        return matched_name, score

    logger.debug(f"No match found for '{name}' (threshold: {threshold})")
    return None


def find_all_matches(
    name: str,
    candidates: List[str],
    threshold: Optional[int] = None,
    limit: int = 5
) -> List[Tuple[str, int]]:
    """
    Find all fuzzy matches for a merchant name above threshold.

    Args:
        name: Normalized name to match
        candidates: List of normalized candidate names
        threshold: Minimum similarity score (0-100)
        limit: Maximum number of matches to return

    Returns:
        List of (matched_name, score) tuples, sorted by score descending
    """
    if not name or not candidates:
        return []

    settings = get_settings()
    threshold = threshold or settings.matching.fuzzy_threshold

    results = process.extract(
        name,
        candidates,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold,
        limit=limit
    )

    return [(match, score) for match, score, _ in results]


def match_merchants(
    simplymiles_merchants: List[str],
    portal_merchants: List[str],
    threshold: Optional[int] = None
) -> Dict[str, Tuple[str, int]]:
    """
    Match SimplyMiles merchants to Portal merchants.

    Args:
        simplymiles_merchants: List of normalized SimplyMiles merchant names
        portal_merchants: List of normalized Portal merchant names
        threshold: Minimum similarity score (0-100)

    Returns:
        Dict mapping simplymiles_merchant -> (portal_merchant, score)
    """
    matches = {}
    unmatched = []

    for sm_merchant in simplymiles_merchants:
        result = find_best_match(sm_merchant, portal_merchants, threshold)
        if result:
            matches[sm_merchant] = result
        else:
            unmatched.append(sm_merchant)

    if unmatched:
        logger.info(f"Unmatched SimplyMiles merchants ({len(unmatched)}): {unmatched[:10]}...")

    logger.info(f"Matched {len(matches)}/{len(simplymiles_merchants)} merchants")

    return matches


def get_canonical_name(name: str) -> str:
    """
    Get canonical name after normalization and alias resolution.
    Useful for deduplication and display.

    Args:
        name: Raw merchant name

    Returns:
        Canonical normalized name
    """
    normalized = normalize_merchant(name)

    # Check if this normalized name is an alias
    settings = get_settings()
    return settings.matching.aliases.get(normalized, normalized)


def extract_merchant_keywords(name: str) -> List[str]:
    """
    Extract keywords from a merchant name for alternative matching.

    Args:
        name: Normalized merchant name

    Returns:
        List of significant keywords
    """
    # Common words to filter out
    stopwords = {
        'the', 'and', 'or', 'of', 'for', 'at', 'to', 'in', 'on',
        'com', 'net', 'org', 'shop', 'store', 'online', 'official'
    }

    words = normalize_merchant(name).split()
    keywords = [w for w in words if w not in stopwords and len(w) > 2]

    return keywords

