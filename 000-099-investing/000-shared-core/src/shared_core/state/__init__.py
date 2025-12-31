"""
State management utilities for alert and notification systems.

Provides:
- StateManager: Persistence for trigger deduplication and reminders
- ArchiveManager: Suppression of actioned alerts
- Digest: Snapshot of emailed signals for reminders
- JSON utilities for safe file I/O
"""

from .archiver import ArchiveEntry, ArchiveManager
from .digest import Digest
from .manager import StateManager
from .utils import (
    parse_iso_datetime,
    safe_read_json,
    safe_write_json,
    utc_now_iso,
)

__all__ = [
    # Utils
    "safe_read_json",
    "safe_write_json",
    "utc_now_iso",
    "parse_iso_datetime",
    # Models
    "Digest",
    "ArchiveEntry",
    # Managers
    "StateManager",
    "ArchiveManager",
]

