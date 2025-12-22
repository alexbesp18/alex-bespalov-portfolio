"""
Archive manager for 009-reversals.

This module is now a re-export of shared_core.state for backward compatibility.
All functionality is provided by shared_core.ArchiveManager and shared_core.ArchiveEntry.
"""

# Re-export from shared_core for backward compatibility
from shared_core.state import (
    ArchiveManager,
    ArchiveEntry,
    safe_read_json,
    safe_write_json,
    parse_iso_datetime,
)

# Also export utility functions with original names for compatibility
_utc_now = lambda: __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
_safe_read_json = safe_read_json
_safe_write_json = safe_write_json
_parse_iso_datetime = parse_iso_datetime

__all__ = [
    "ArchiveManager",
    "ArchiveEntry",
    "_utc_now",
    "_safe_read_json",
    "_safe_write_json",
    "_parse_iso_datetime",
]
