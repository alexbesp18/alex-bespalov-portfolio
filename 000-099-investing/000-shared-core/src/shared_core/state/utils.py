"""
JSON and datetime utilities for state management.

These are low-level utilities used by StateManager and ArchiveManager.
"""

import json
import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def utc_now() -> datetime:
    """Return current UTC time as datetime object."""
    return datetime.now(timezone.utc)


def parse_iso_datetime(value: str) -> Optional[datetime]:
    """
    Parse an ISO 8601 datetime string to datetime object.

    Handles:
    - Trailing 'Z' suffix
    - Missing timezone (assumes UTC)

    Args:
        value: ISO datetime string

    Returns:
        datetime object with UTC timezone, or None if parsing fails
    """
    try:
        if not value:
            return None
        # Tolerate trailing 'Z'
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError) as e:
        logger.debug(f"Failed to parse ISO datetime '{value}': {e}")
        return None


def safe_read_json(path: str) -> Optional[Dict[str, Any]]:
    """
    Safely read JSON from a file.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON as dict, or None if file doesn't exist or parsing fails
    """
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON at {path}: {e}")
        return None
    except OSError as e:
        logger.warning(f"Failed to read file at {path}: {e}")
        return None


def safe_write_json(path: str, data: Dict[str, Any]) -> None:
    """
    Safely write JSON to a file with atomic replace.

    Uses a temporary file and os.replace() to ensure atomicity.
    Creates parent directories if they don't exist.

    Args:
        path: Target file path
        data: Dictionary to serialize as JSON
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp_path, path)

