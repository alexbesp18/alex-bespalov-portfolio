"""
Unit tests for shared_core.state module.

Tests StateManager, ArchiveManager, Digest, and JSON utilities.
"""

import pytest
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from shared_core.state import (
    StateManager,
    ArchiveManager,
    ArchiveEntry,
    Digest,
    safe_read_json,
    safe_write_json,
    utc_now_iso,
    parse_iso_datetime,
)


class TestJsonUtils:
    """Tests for JSON utility functions."""
    
    def test_safe_read_json_handles_missing_file(self, tmp_path):
        """safe_read_json returns None for non-existent file."""
        path = str(tmp_path / "nonexistent.json")
        result = safe_read_json(path)
        assert result is None
    
    def test_safe_read_json_handles_corrupt_json(self, tmp_path):
        """safe_read_json returns None for malformed JSON."""
        path = tmp_path / "corrupt.json"
        path.write_text("{ invalid json }")
        result = safe_read_json(str(path))
        assert result is None
    
    def test_safe_read_json_reads_valid_json(self, tmp_path):
        """safe_read_json correctly parses valid JSON."""
        path = tmp_path / "valid.json"
        data = {"key": "value", "number": 42}
        path.write_text(json.dumps(data))
        result = safe_read_json(str(path))
        assert result == data
    
    def test_safe_write_json_creates_dirs(self, tmp_path):
        """safe_write_json creates parent directories."""
        path = str(tmp_path / "nested" / "dir" / "file.json")
        data = {"test": True}
        safe_write_json(path, data)
        
        assert os.path.exists(path)
        with open(path) as f:
            assert json.load(f) == data
    
    def test_safe_write_json_atomic(self, tmp_path):
        """safe_write_json uses atomic replace (no partial writes)."""
        path = str(tmp_path / "atomic.json")
        data = {"key": "value"}
        safe_write_json(path, data)
        
        # No .tmp file should remain
        assert not os.path.exists(f"{path}.tmp")
        assert os.path.exists(path)
    
    def test_utc_now_iso_format(self):
        """utc_now_iso returns valid ISO 8601 string."""
        result = utc_now_iso()
        # Should be parseable
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo is not None
        # Should be recent
        assert (datetime.now(timezone.utc) - parsed).total_seconds() < 5
    
    def test_parse_iso_datetime_handles_Z_suffix(self):
        """parse_iso_datetime handles 'Z' suffix (Zulu time)."""
        result = parse_iso_datetime("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.tzinfo is not None
        assert result.hour == 10
    
    def test_parse_iso_datetime_handles_missing_tz(self):
        """parse_iso_datetime assumes UTC for naive datetimes."""
        result = parse_iso_datetime("2024-01-15T10:30:00")
        assert result is not None
        assert result.tzinfo == timezone.utc
    
    def test_parse_iso_datetime_handles_offset(self):
        """parse_iso_datetime handles timezone offsets."""
        result = parse_iso_datetime("2024-01-15T10:30:00+05:00")
        assert result is not None
        assert result.tzinfo is not None
    
    def test_parse_iso_datetime_handles_empty(self):
        """parse_iso_datetime returns None for empty string."""
        assert parse_iso_datetime("") is None
        assert parse_iso_datetime(None) is None  # type: ignore
    
    def test_parse_iso_datetime_handles_invalid(self):
        """parse_iso_datetime returns None for invalid strings."""
        assert parse_iso_datetime("not a date") is None
        assert parse_iso_datetime("2024-13-45") is None


class TestStateManager:
    """Tests for StateManager class."""
    
    def test_load_creates_default_on_missing_file(self, tmp_state_path):
        """load() creates default state when file doesn't exist."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        
        assert "version" in state
        assert "last_run" in state
        assert "seen_triggers" in state
        assert "last_digest" in state
        assert "last_reminder" in state
    
    def test_load_preserves_existing_state(self, tmp_state_path):
        """load() preserves data from existing state file."""
        # Pre-populate state file
        existing = {
            "version": 1,
            "last_run": {"ran_at": "2024-01-01T00:00:00+00:00", "trigger_keys": ["TEST:SIGNAL"]},
            "seen_triggers": {"TEST:SIGNAL": {"first_seen": "2024-01-01"}},
            "last_digest": None,
            "last_reminder": None,
        }
        with open(tmp_state_path, "w") as f:
            json.dump(existing, f)
        
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        
        assert state["last_run"]["trigger_keys"] == ["TEST:SIGNAL"]
        assert "TEST:SIGNAL" in state["seen_triggers"]
    
    def test_save_creates_parent_dirs(self, tmp_path):
        """save() creates parent directories if needed."""
        path = str(tmp_path / "nested" / "state.json")
        mgr = StateManager(path)
        state = mgr.load()
        mgr.save(state)
        
        assert os.path.exists(path)
    
    def test_set_last_run_updates_timestamp(self, tmp_state_path):
        """set_last_run() updates timestamp and trigger keys."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        
        keys = ["A:SIGNAL", "B:SIGNAL"]
        mgr.set_last_run(state, keys)
        
        assert state["last_run"]["trigger_keys"] == keys
        assert state["last_run"]["ran_at"] is not None
        # Verify timestamp is recent
        parsed = parse_iso_datetime(state["last_run"]["ran_at"])
        assert (datetime.now(timezone.utc) - parsed).total_seconds() < 5
    
    def test_get_last_run_trigger_keys(self, tmp_state_path):
        """get_last_run_trigger_keys() returns stored keys."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        
        mgr.set_last_run(state, ["KEY1", "KEY2"])
        result = mgr.get_last_run_trigger_keys(state)
        
        assert result == ["KEY1", "KEY2"]
    
    def test_get_last_run_trigger_keys_empty(self, tmp_state_path):
        """get_last_run_trigger_keys() returns empty list on fresh state."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        result = mgr.get_last_run_trigger_keys(state)
        assert result == []
    
    def test_update_seen_triggers_creates_new(self, tmp_state_path, sample_triggered_signals):
        """update_seen_triggers() creates new entries."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        
        mgr.update_seen_triggers(state, sample_triggered_signals)
        
        assert "NVDA_score_above_BUY_7" in state["seen_triggers"]
        entry = state["seen_triggers"]["NVDA_score_above_BUY_7"]
        assert entry["symbol"] == "NVDA"
        assert "first_seen" in entry
        assert "last_seen" in entry
    
    def test_update_seen_triggers_deduplicates(self, tmp_state_path):
        """update_seen_triggers() updates existing entries."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        
        # First update
        signals1 = [{"symbol": "NVDA", "trigger_key": "KEY1", "message": "First"}]
        mgr.update_seen_triggers(state, signals1)
        first_seen = state["seen_triggers"]["KEY1"]["first_seen"]
        
        # Second update with same key
        signals2 = [{"symbol": "NVDA", "trigger_key": "KEY1", "message": "Second"}]
        mgr.update_seen_triggers(state, signals2)
        
        # first_seen should be preserved, message updated
        assert state["seen_triggers"]["KEY1"]["first_seen"] == first_seen
        assert state["seen_triggers"]["KEY1"]["last_message"] == "Second"
    
    def test_set_last_digest(self, tmp_state_path):
        """set_last_digest() stores digest correctly."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        
        digest = Digest(
            digest_id="2024-01-15",
            sent_at=utc_now_iso(),
            results=[{"symbol": "NVDA", "action": "BUY"}],
            buy_count=1,
            sell_count=0,
        )
        mgr.set_last_digest(state, digest)
        
        assert state["last_digest"]["digest_id"] == "2024-01-15"
        assert state["last_digest"]["buy_count"] == 1
    
    def test_get_last_digest(self, tmp_state_path):
        """get_last_digest() retrieves stored digest."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        
        digest = Digest(
            digest_id="2024-01-15",
            sent_at=utc_now_iso(),
            results=[{"symbol": "NVDA"}],
            buy_count=1,
            sell_count=0,
        )
        mgr.set_last_digest(state, digest)
        
        retrieved = mgr.get_last_digest(state)
        assert retrieved is not None
        assert retrieved.digest_id == "2024-01-15"
    
    def test_get_last_digest_returns_none(self, tmp_state_path):
        """get_last_digest() returns None when no digest stored."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        assert mgr.get_last_digest(state) is None
    
    def test_should_send_reminder_no_digest(self, tmp_state_path):
        """should_send_reminder() returns False when no digest."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        assert mgr.should_send_reminder(state) is False
    
    def test_should_send_reminder_empty_results(self, tmp_state_path):
        """should_send_reminder() returns False when digest has no results."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        
        digest = Digest(
            digest_id="2024-01-15",
            sent_at=utc_now_iso(),
            results=[],
            buy_count=0,
            sell_count=0,
        )
        mgr.set_last_digest(state, digest)
        
        assert mgr.should_send_reminder(state) is False
    
    def test_should_send_reminder_stale_digest(self, tmp_state_path):
        """should_send_reminder() returns False for stale digest (>36h)."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        
        old_time = (datetime.now(timezone.utc) - timedelta(hours=40)).isoformat()
        digest = Digest(
            digest_id="2024-01-15",
            sent_at=old_time,
            results=[{"symbol": "NVDA"}],
            buy_count=1,
            sell_count=0,
        )
        mgr.set_last_digest(state, digest)
        
        assert mgr.should_send_reminder(state) is False
    
    def test_should_send_reminder_prevents_duplicates(self, tmp_state_path):
        """should_send_reminder() returns False after reminder sent."""
        mgr = StateManager(tmp_state_path)
        state = mgr.load()
        
        digest = Digest(
            digest_id="2024-01-15",
            sent_at=utc_now_iso(),
            results=[{"symbol": "NVDA"}],
            buy_count=1,
            sell_count=0,
        )
        mgr.set_last_digest(state, digest)
        
        # First check: should send
        assert mgr.should_send_reminder(state) is True
        
        # Mark reminder sent
        mgr.mark_reminder_sent(state, "2024-01-15")
        
        # Second check: should not send again
        assert mgr.should_send_reminder(state) is False
    
    def test_state_persists_across_instances(self, tmp_state_path):
        """State changes persist when loading in new manager instance."""
        # First instance: set some state
        mgr1 = StateManager(tmp_state_path)
        state1 = mgr1.load()
        mgr1.set_last_run(state1, ["TEST:SIGNAL"])
        mgr1.save(state1)
        
        # Second instance: verify state persisted
        mgr2 = StateManager(tmp_state_path)
        state2 = mgr2.load()
        assert mgr2.get_last_run_trigger_keys(state2) == ["TEST:SIGNAL"]


class TestDigest:
    """Tests for Digest dataclass."""
    
    def test_to_dict_contains_all_fields(self):
        """to_dict() includes all fields."""
        digest = Digest(
            digest_id="2024-01-15",
            sent_at="2024-01-15T16:00:00+00:00",
            results=[{"symbol": "NVDA"}],
            buy_count=1,
            sell_count=2,
        )
        d = digest.to_dict()
        
        assert d["digest_id"] == "2024-01-15"
        assert d["sent_at"] == "2024-01-15T16:00:00+00:00"
        assert d["results"] == [{"symbol": "NVDA"}]
        assert d["buy_count"] == 1
        assert d["sell_count"] == 2
    
    def test_from_dict_roundtrip(self):
        """from_dict() correctly recreates Digest from dict."""
        original = Digest(
            digest_id="2024-01-15",
            sent_at="2024-01-15T16:00:00+00:00",
            results=[{"symbol": "NVDA", "action": "BUY"}],
            buy_count=1,
            sell_count=0,
        )
        
        recreated = Digest.from_dict(original.to_dict())
        
        assert recreated.digest_id == original.digest_id
        assert recreated.sent_at == original.sent_at
        assert recreated.results == original.results
        assert recreated.buy_count == original.buy_count


class TestArchiveManager:
    """Tests for ArchiveManager class."""
    
    def test_load_creates_default(self, tmp_archive_path):
        """load() creates default archive when file missing."""
        mgr = ArchiveManager(tmp_archive_path)
        archive = mgr.load()
        
        assert "version" in archive
        assert "executed" in archive
        assert archive["executed"] == []
    
    def test_is_suppressed_within_window(self, tmp_archive_path):
        """is_suppressed() returns True within suppression window."""
        mgr = ArchiveManager(tmp_archive_path)
        archive = mgr.load()
        
        mgr.archive_trigger(archive, "NVDA", "KEY1", "Test message", suppress_days=30)
        
        assert mgr.is_suppressed(archive, "KEY1") is True
    
    def test_is_suppressed_after_expiry(self, tmp_archive_path):
        """is_suppressed() returns False after expiration."""
        mgr = ArchiveManager(tmp_archive_path)
        archive = mgr.load()
        
        # Manually create an expired entry
        expired = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        archive["executed"] = [{
            "symbol": "NVDA",
            "trigger_key": "KEY1",
            "trigger_message": "Test",
            "executed_at": expired,
            "suppress_until": expired,
        }]
        
        assert mgr.is_suppressed(archive, "KEY1") is False
    
    def test_is_suppressed_unknown_key(self, tmp_archive_path):
        """is_suppressed() returns False for unknown key."""
        mgr = ArchiveManager(tmp_archive_path)
        archive = mgr.load()
        
        assert mgr.is_suppressed(archive, "UNKNOWN_KEY") is False
    
    def test_archive_trigger_adds_entry(self, tmp_archive_path):
        """archive_trigger() adds new entry."""
        mgr = ArchiveManager(tmp_archive_path)
        archive = mgr.load()
        
        mgr.archive_trigger(archive, "NVDA", "KEY1", "Test message", suppress_days=30)
        
        assert len(archive["executed"]) == 1
        entry = archive["executed"][0]
        assert entry["symbol"] == "NVDA"
        assert entry["trigger_key"] == "KEY1"
    
    def test_archive_trigger_extends_existing(self, tmp_archive_path):
        """archive_trigger() extends suppression for existing key."""
        mgr = ArchiveManager(tmp_archive_path)
        archive = mgr.load()
        
        # First archive
        mgr.archive_trigger(archive, "NVDA", "KEY1", "First", suppress_days=10)
        first_until = archive["executed"][0]["suppress_until"]
        
        # Second archive with same key
        mgr.archive_trigger(archive, "NVDA", "KEY1", "Second", suppress_days=30)
        
        # Should still be one entry, but extended
        assert len(archive["executed"]) == 1
        assert archive["executed"][0]["trigger_message"] == "Second"
        assert archive["executed"][0]["suppress_until"] != first_until
    
    def test_cleanup_expired_removes_old(self, tmp_archive_path):
        """cleanup_expired() removes expired entries."""
        mgr = ArchiveManager(tmp_archive_path)
        archive = mgr.load()
        
        # Create one expired and one valid entry
        now = datetime.now(timezone.utc)
        expired = (now - timedelta(days=1)).isoformat()
        valid = (now + timedelta(days=30)).isoformat()
        
        archive["executed"] = [
            {"trigger_key": "EXPIRED", "suppress_until": expired},
            {"trigger_key": "VALID", "suppress_until": valid},
        ]
        
        removed = mgr.cleanup_expired(archive)
        
        assert removed == 1
        assert len(archive["executed"]) == 1
        assert archive["executed"][0]["trigger_key"] == "VALID"
    
    def test_get_archived_triggers(self, tmp_archive_path):
        """get_archived_triggers() returns ArchiveEntry objects."""
        mgr = ArchiveManager(tmp_archive_path)
        archive = mgr.load()
        
        mgr.archive_trigger(archive, "NVDA", "KEY1", "Test", 30)
        mgr.archive_trigger(archive, "AAPL", "KEY2", "Test2", 30)
        
        entries = mgr.get_archived_triggers(archive)
        
        assert len(entries) == 2
        assert all(isinstance(e, ArchiveEntry) for e in entries)
        assert entries[0].symbol == "NVDA"
    
    def test_archive_persists_across_instances(self, tmp_archive_path):
        """Archive changes persist when loading in new manager instance."""
        # First instance
        mgr1 = ArchiveManager(tmp_archive_path)
        archive1 = mgr1.load()
        mgr1.archive_trigger(archive1, "NVDA", "KEY1", "Test", 30)
        mgr1.save(archive1)
        
        # Second instance
        mgr2 = ArchiveManager(tmp_archive_path)
        archive2 = mgr2.load()
        assert mgr2.is_suppressed(archive2, "KEY1") is True


class TestArchiveEntry:
    """Tests for ArchiveEntry dataclass."""
    
    def test_to_dict_roundtrip(self):
        """to_dict() and from_dict() roundtrip correctly."""
        original = ArchiveEntry(
            symbol="NVDA",
            trigger_key="KEY1",
            trigger_message="Test",
            executed_at="2024-01-15T16:00:00+00:00",
            suppress_until="2024-02-14T16:00:00+00:00",
        )
        
        recreated = ArchiveEntry.from_dict(original.to_dict())
        
        assert recreated.symbol == original.symbol
        assert recreated.trigger_key == original.trigger_key
        assert recreated.suppress_until == original.suppress_until

