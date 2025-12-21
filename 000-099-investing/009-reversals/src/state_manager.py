import json
import os
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    try:
        if not value:
            return None
        # tolerate trailing 'Z'
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _safe_read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read state json at {path}: {e}")
        return None


def _safe_write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


@dataclass
class Digest:
    """
    Persisted snapshot of what we emailed at the main (4pm) run.
    Used by the next-day reminder email without re-fetching market data.
    """
    digest_id: str  # e.g. "2025-12-14"
    sent_at: str    # ISO timestamp (UTC)
    results: List[Dict[str, Any]]
    buy_count: int
    sell_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "digest_id": self.digest_id,
            "sent_at": self.sent_at,
            "results": self.results,
            "buy_count": self.buy_count,
            "sell_count": self.sell_count,
        }


class StateManager:
    """
    Minimal persistence layer to prevent repeated alerts and support reminders.

    State file lives at: sentinel/data/state.json (relative to repo root).
    """

    VERSION = 1

    def __init__(self, state_path: str):
        self.state_path = state_path

    def load(self) -> Dict[str, Any]:
        data = _safe_read_json(self.state_path)
        if not data:
            return self._default_state()
        if data.get("version") != self.VERSION:
            # Forward-compat: keep unknown keys but ensure required structure exists.
            data["version"] = self.VERSION
        data.setdefault("last_run", {})
        data.setdefault("seen_triggers", {})
        data.setdefault("last_digest", None)
        data.setdefault("last_reminder", None)
        return data

    def save(self, state: Dict[str, Any]) -> None:
        state["version"] = self.VERSION
        _safe_write_json(self.state_path, state)

    def get_last_run_trigger_keys(self, state: Dict[str, Any]) -> List[str]:
        last_run = state.get("last_run") or {}
        keys = last_run.get("trigger_keys") or []
        return list(keys)

    def set_last_run(self, state: Dict[str, Any], trigger_keys: List[str]) -> None:
        state["last_run"] = {
            "ran_at": _utc_now_iso(),
            "trigger_keys": trigger_keys,
        }

    def update_seen_triggers(self, state: Dict[str, Any], triggered: List[Dict[str, Any]]) -> None:
        """
        `triggered` items are expected to include:
          - symbol
          - trigger_key (stable identifier)
          - message (human readable)
        """
        seen = state.setdefault("seen_triggers", {})
        now = _utc_now_iso()
        for item in triggered:
            key = item.get("trigger_key")
            if not key:
                continue
            existing = seen.get(key)
            if not existing:
                seen[key] = {
                    "symbol": item.get("symbol"),
                    "first_seen": now,
                    "last_seen": now,
                    "last_message": item.get("message"),
                }
            else:
                existing["last_seen"] = now
                existing["last_message"] = item.get("message")

    def set_last_digest(self, state: Dict[str, Any], digest: Digest) -> None:
        state["last_digest"] = digest.to_dict()

    def mark_reminder_sent(self, state: Dict[str, Any], digest_id: str) -> None:
        state["last_reminder"] = {"digest_id": digest_id, "sent_at": _utc_now_iso()}

    def should_send_reminder(self, state: Dict[str, Any]) -> bool:
        """
        User preference: send reminder only if triggers existed.
        Also prevent duplicate reminders (DST double-cron).
        """
        last_digest = state.get("last_digest")
        if not last_digest:
            return False
        results = last_digest.get("results") or []
        if len(results) == 0:
            return False

        digest_id = last_digest.get("digest_id")
        if not digest_id:
            return False

        # Don't remind on stale digests (weekends / missed runs). 36h window.
        sent_at = _parse_iso_datetime(last_digest.get("sent_at"))
        if sent_at:
            age_hours = (datetime.now(timezone.utc) - sent_at.astimezone(timezone.utc)).total_seconds() / 3600
            if age_hours > 36:
                return False

        last_reminder = state.get("last_reminder") or {}
        if last_reminder.get("digest_id") == digest_id:
            return False

        return True

    def _default_state(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "last_run": {"ran_at": None, "trigger_keys": []},
            "seen_triggers": {},
            "last_digest": None,
            "last_reminder": None,
        }


