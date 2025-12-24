"""
StateManager for alert deduplication and reminder support.

Provides persistence layer to:
- Prevent repeated alerts (deduplication)
- Track seen triggers with first/last seen timestamps
- Store digest snapshots for reminder emails
- Manage reminder state to prevent duplicate reminders
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from .utils import safe_read_json, safe_write_json, utc_now_iso, parse_iso_datetime
from .digest import Digest

logger = logging.getLogger(__name__)


class StateManager:
    """
    Minimal persistence layer to prevent repeated alerts and support reminders.

    State file structure:
    {
        "version": 1,
        "last_run": {
            "ran_at": "2025-12-14T16:00:00+00:00",
            "trigger_keys": ["NVDA:BUY_PULLBACK", ...]
        },
        "seen_triggers": {
            "NVDA:BUY_PULLBACK": {
                "symbol": "NVDA",
                "first_seen": "2025-12-10T...",
                "last_seen": "2025-12-14T...",
                "last_message": "BUY: Score 8.5 >= 7"
            }
        },
        "last_digest": { ... },
        "last_reminder": { "digest_id": "...", "sent_at": "..." }
    }

    Attributes:
        state_path: Path to the state JSON file
    """

    VERSION = 1

    def __init__(self, state_path: str):
        """
        Initialize StateManager.

        Args:
            state_path: Path to state JSON file (will be created if missing)
        """
        self.state_path = state_path

    def load(self) -> Dict[str, Any]:
        """
        Load state from disk.

        Returns:
            State dictionary with all required keys populated
        """
        data = safe_read_json(self.state_path)
        if not data:
            return self._default_state()
        if data.get("version") != self.VERSION:
            data["version"] = self.VERSION
        data.setdefault("last_run", {})
        data.setdefault("seen_triggers", {})
        data.setdefault("last_digest", None)
        data.setdefault("last_reminder", None)
        return data

    def save(self, state: Dict[str, Any]) -> None:
        """
        Persist state to disk.

        Args:
            state: State dictionary to save
        """
        state["version"] = self.VERSION
        safe_write_json(self.state_path, state)

    def get_last_run_trigger_keys(self, state: Dict[str, Any]) -> List[str]:
        """
        Get trigger keys from the last run.

        Args:
            state: Current state dictionary

        Returns:
            List of trigger keys that fired in the last run
        """
        last_run = state.get("last_run") or {}
        keys = last_run.get("trigger_keys") or []
        return list(keys)

    def set_last_run(self, state: Dict[str, Any], trigger_keys: List[str]) -> None:
        """
        Record trigger keys from current run.

        Args:
            state: Current state dictionary (modified in place)
            trigger_keys: List of trigger keys that fired
        """
        state["last_run"] = {
            "ran_at": utc_now_iso(),
            "trigger_keys": trigger_keys,
        }

    def update_seen_triggers(
        self, state: Dict[str, Any], triggered: List[Dict[str, Any]]
    ) -> None:
        """
        Update seen triggers with new trigger events.

        Args:
            state: Current state dictionary (modified in place)
            triggered: List of trigger dicts with keys:
                - symbol: Ticker symbol
                - trigger_key: Stable identifier for deduplication
                - message: Human-readable trigger message
        """
        seen = state.setdefault("seen_triggers", {})
        now = utc_now_iso()

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
        """
        Store digest snapshot for reminder emails.

        Args:
            state: Current state dictionary (modified in place)
            digest: Digest object to store
        """
        state["last_digest"] = digest.to_dict()

    def get_last_digest(self, state: Dict[str, Any]) -> Digest | None:
        """
        Retrieve last digest if available.

        Args:
            state: Current state dictionary

        Returns:
            Digest object or None
        """
        data = state.get("last_digest")
        if not data:
            return None
        return Digest.from_dict(data)

    def mark_reminder_sent(self, state: Dict[str, Any], digest_id: str) -> None:
        """
        Mark that a reminder was sent for a digest.

        Args:
            state: Current state dictionary (modified in place)
            digest_id: ID of the digest that was reminded
        """
        state["last_reminder"] = {"digest_id": digest_id, "sent_at": utc_now_iso()}

    def should_send_reminder(self, state: Dict[str, Any]) -> bool:
        """
        Determine if a reminder email should be sent.

        Rules:
        - Must have a last_digest with results
        - Digest must not be stale (>36 hours old)
        - Reminder must not have been sent for this digest yet

        Args:
            state: Current state dictionary

        Returns:
            True if reminder should be sent
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
        sent_at = parse_iso_datetime(last_digest.get("sent_at"))
        if sent_at:
            now = datetime.now(timezone.utc)
            age_hours = (now - sent_at.astimezone(timezone.utc)).total_seconds() / 3600
            if age_hours > 36:
                return False

        # Don't send duplicate reminders
        last_reminder = state.get("last_reminder") or {}
        if last_reminder.get("digest_id") == digest_id:
            return False

        return True

    def _default_state(self) -> Dict[str, Any]:
        """Create default empty state."""
        return {
            "version": self.VERSION,
            "last_run": {"ran_at": None, "trigger_keys": []},
            "seen_triggers": {},
            "last_digest": None,
            "last_reminder": None,
        }

