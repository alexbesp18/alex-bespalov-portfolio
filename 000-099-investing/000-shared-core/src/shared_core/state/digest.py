"""
Digest model for email notification snapshots.

A Digest captures what was emailed at a main run,
enabling reminder emails without re-fetching market data.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Digest:
    """
    Persisted snapshot of what we emailed at the main run.
    Used by the next-day reminder email without re-fetching market data.

    Attributes:
        digest_id: Unique identifier, typically date string (e.g., "2025-12-14")
        sent_at: ISO timestamp (UTC) when the digest was sent
        results: List of signal/alert dicts that were emailed
        buy_count: Number of buy signals in this digest
        sell_count: Number of sell signals in this digest
    """
    digest_id: str
    sent_at: str
    results: List[Dict[str, Any]]
    buy_count: int
    sell_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "digest_id": self.digest_id,
            "sent_at": self.sent_at,
            "results": self.results,
            "buy_count": self.buy_count,
            "sell_count": self.sell_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Digest":
        """Create Digest from dictionary."""
        return cls(
            digest_id=data.get("digest_id", ""),
            sent_at=data.get("sent_at", ""),
            results=data.get("results", []),
            buy_count=data.get("buy_count", 0),
            sell_count=data.get("sell_count", 0),
        )

