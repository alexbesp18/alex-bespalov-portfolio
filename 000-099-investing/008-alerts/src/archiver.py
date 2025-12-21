import json
import os
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read archive json at {path}: {e}")
        return None


def _safe_write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    try:
        if not value:
            return None
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


@dataclass
class ArchiveEntry:
    symbol: str
    trigger_key: str
    trigger_message: str
    executed_at: str         # ISO (UTC)
    suppress_until: str      # ISO (UTC)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "trigger_key": self.trigger_key,
            "trigger_message": self.trigger_message,
            "executed_at": self.executed_at,
            "suppress_until": self.suppress_until,
        }


class ArchiveManager:
    VERSION = 1

    def __init__(self, archive_path: str):
        self.archive_path = archive_path

    def load(self) -> Dict[str, Any]:
        data = _safe_read_json(self.archive_path)
        if not data:
            return {"version": self.VERSION, "executed": []}
        data["version"] = self.VERSION
        data.setdefault("executed", [])
        return data

    def save(self, data: Dict[str, Any]) -> None:
        data["version"] = self.VERSION
        _safe_write_json(self.archive_path, data)

    def is_suppressed(self, archive: Dict[str, Any], trigger_key: str, now: Optional[datetime] = None) -> bool:
        now = now or _utc_now()
        for e in archive.get("executed") or []:
            if e.get("trigger_key") != trigger_key:
                continue
            until = _parse_iso_datetime(e.get("suppress_until"))
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

        # Dedup: if same trigger_key exists, extend suppression window (don’t append duplicates)
        for existing in executed:
            if existing.get("trigger_key") == trigger_key:
                existing["symbol"] = symbol
                existing["trigger_message"] = trigger_message
                existing["executed_at"] = entry.executed_at
                existing["suppress_until"] = entry.suppress_until
                return

        executed.append(entry.to_dict())


