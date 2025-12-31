"""
ArchiveManager for suppressing actioned alerts.

When a user acts on an alert (e.g., executes a trade),
the alert can be archived to suppress it for a configurable period.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .utils import parse_iso_datetime, safe_read_json, safe_write_json

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


@dataclass
class ArchiveEntry:
    """
    Record of an actioned/archived alert.

    Attributes:
        symbol: Ticker symbol (e.g., "NVDA")
        trigger_key: Stable trigger identifier for matching
        trigger_message: Human-readable trigger description
        executed_at: ISO timestamp when user actioned the alert
        suppress_until: ISO timestamp until which to suppress this trigger
    """
    symbol: str
    trigger_key: str
    trigger_message: str
    executed_at: str
    suppress_until: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "symbol": self.symbol,
            "trigger_key": self.trigger_key,
            "trigger_message": self.trigger_message,
            "executed_at": self.executed_at,
            "suppress_until": self.suppress_until,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArchiveEntry":
        """Create ArchiveEntry from dictionary."""
        return cls(
            symbol=data.get("symbol", ""),
            trigger_key=data.get("trigger_key", ""),
            trigger_message=data.get("trigger_message", ""),
            executed_at=data.get("executed_at", ""),
            suppress_until=data.get("suppress_until", ""),
        )


class ArchiveManager:
    """
    Manager for archived/actioned alerts.

    Archive file structure:
    {
        "version": 1,
        "executed": [
            {
                "symbol": "NVDA",
                "trigger_key": "NVDA_score_above_BUY_7",
                "trigger_message": "BUY: Score 8.5 >= 7",
                "executed_at": "2025-12-14T16:30:00+00:00",
                "suppress_until": "2026-01-13T16:30:00+00:00"
            }
        ]
    }

    Attributes:
        archive_path: Path to the archive JSON file
    """

    VERSION = 1

    def __init__(self, archive_path: str):
        """
        Initialize ArchiveManager.

        Args:
            archive_path: Path to archive JSON file (created if missing)
        """
        self.archive_path = archive_path

    def load(self) -> Dict[str, Any]:
        """
        Load archive from disk.

        Returns:
            Archive dictionary with all required keys
        """
        data = safe_read_json(self.archive_path)
        if not data:
            return {"version": self.VERSION, "executed": []}
        data["version"] = self.VERSION
        data.setdefault("executed", [])
        return data

    def save(self, data: Dict[str, Any]) -> None:
        """
        Persist archive to disk.

        Args:
            data: Archive dictionary to save
        """
        data["version"] = self.VERSION
        safe_write_json(self.archive_path, data)

    def is_suppressed(
        self,
        archive: Dict[str, Any],
        trigger_key: str,
        now: Optional[datetime] = None,
    ) -> bool:
        """
        Check if a trigger is currently suppressed.

        Args:
            archive: Archive dictionary
            trigger_key: Trigger key to check
            now: Current time (defaults to UTC now)

        Returns:
            True if trigger should be suppressed
        """
        now = now or _utc_now()
        for e in archive.get("executed") or []:
            if e.get("trigger_key") != trigger_key:
                continue
            until = parse_iso_datetime(e.get("suppress_until"))
            if until and now <= until.astimezone(timezone.utc):
                return True
        return False

    def archive_trigger(
        self,
        archive: Dict[str, Any],
        symbol: str,
        trigger_key: str,
        trigger_message: str,
        suppress_days: int = 30,
    ) -> None:
        """
        Archive a trigger to suppress it for a period.

        If the trigger already exists, extends the suppression window.

        Args:
            archive: Archive dictionary (modified in place)
            symbol: Ticker symbol
            trigger_key: Stable trigger identifier
            trigger_message: Human-readable description
            suppress_days: Days to suppress (default 30)
        """
        now = _utc_now()
        suppress_until = now + timedelta(days=suppress_days)

        entry = ArchiveEntry(
            symbol=symbol,
            trigger_key=trigger_key,
            trigger_message=trigger_message,
            executed_at=now.isoformat(),
            suppress_until=suppress_until.isoformat(),
        )

        executed: List[Dict[str, Any]] = archive.setdefault("executed", [])

        # Dedup: if same trigger_key exists, update instead of append
        for existing in executed:
            if existing.get("trigger_key") == trigger_key:
                existing["symbol"] = symbol
                existing["trigger_message"] = trigger_message
                existing["executed_at"] = entry.executed_at
                existing["suppress_until"] = entry.suppress_until
                return

        executed.append(entry.to_dict())

    def get_archived_triggers(self, archive: Dict[str, Any]) -> List[ArchiveEntry]:
        """
        Get all archived triggers.

        Args:
            archive: Archive dictionary

        Returns:
            List of ArchiveEntry objects
        """
        return [
            ArchiveEntry.from_dict(e)
            for e in archive.get("executed", [])
        ]

    def cleanup_expired(
        self,
        archive: Dict[str, Any],
        now: Optional[datetime] = None,
    ) -> int:
        """
        Remove expired archive entries.

        Args:
            archive: Archive dictionary (modified in place)
            now: Current time (defaults to UTC now)

        Returns:
            Number of entries removed
        """
        now = now or _utc_now()
        executed = archive.get("executed", [])
        original_count = len(executed)

        archive["executed"] = [
            e for e in executed
            if (until := parse_iso_datetime(e.get("suppress_until")))
            and now <= until.astimezone(timezone.utc)
        ]

        return original_count - len(archive["executed"])

