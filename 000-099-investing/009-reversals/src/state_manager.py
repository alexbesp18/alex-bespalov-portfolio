"""
State manager for 009-reversals.

This module is now a re-export of shared_core.state for backward compatibility.
All functionality is provided by shared_core.StateManager and shared_core.Digest.
"""

# Re-export from shared_core for backward compatibility
from shared_core.state import (
    StateManager,
    Digest,
    safe_read_json,
    safe_write_json,
    utc_now_iso,
    parse_iso_datetime,
)

# Also export utility functions with original names for compatibility
_utc_now_iso = utc_now_iso
_parse_iso_datetime = parse_iso_datetime
_safe_read_json = safe_read_json
_safe_write_json = safe_write_json

__all__ = [
    "StateManager",
    "Digest",
    "_utc_now_iso",
    "_parse_iso_datetime", 
    "_safe_read_json",
    "_safe_write_json",
]
