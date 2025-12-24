"""
Watchlist models for ticker configuration.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WatchlistEntry:
    """
    A single ticker entry in a watchlist.

    Attributes:
        symbol: Ticker symbol
        list_type: Type of list (portfolio, watchlist, etc.)
        triggers: Custom triggers for this ticker
        notes: User notes about this ticker
    """
    symbol: str
    list_type: str = "watchlist"
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "list_type": self.list_type,
            "triggers": self.triggers,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WatchlistEntry":
        """Create from dictionary."""
        return cls(
            symbol=data.get("symbol", ""),
            list_type=data.get("list_type", "watchlist"),
            triggers=data.get("triggers", []),
            notes=data.get("notes", ""),
        )


@dataclass
class Watchlist:
    """
    Collection of ticker entries with configuration.

    Attributes:
        entries: List of WatchlistEntry objects
        default_triggers: Default triggers applied to all tickers
        metadata: Additional configuration
    """
    entries: List[WatchlistEntry] = field(default_factory=list)
    default_triggers: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def symbols(self) -> List[str]:
        """Get list of all symbols."""
        return [e.symbol for e in self.entries]

    @property
    def portfolio(self) -> List[WatchlistEntry]:
        """Get portfolio entries only."""
        return [e for e in self.entries if e.list_type == "portfolio"]

    @property
    def watchlist(self) -> List[WatchlistEntry]:
        """Get watchlist entries only."""
        return [e for e in self.entries if e.list_type == "watchlist"]

    def get_entry(self, symbol: str) -> Optional[WatchlistEntry]:
        """Get entry by symbol."""
        for e in self.entries:
            if e.symbol.upper() == symbol.upper():
                return e
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entries": [e.to_dict() for e in self.entries],
            "default_triggers": self.default_triggers,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Watchlist":
        """Create from dictionary."""
        entries = [WatchlistEntry.from_dict(e) for e in data.get("entries", [])]
        return cls(
            entries=entries,
            default_triggers=data.get("default_triggers", []),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json_file(cls, path: str) -> "Watchlist":
        """
        Load watchlist from JSON file.

        Supports two formats:
        1. New format: {"entries": [...], "default_triggers": [...]}
        2. Legacy format: {"portfolio": [...], "watchlist": [...]}
        """
        if not os.path.exists(path):
            return cls()

        with open(path, "r") as f:
            data = json.load(f)

        # Check for new format
        if "entries" in data:
            return cls.from_dict(data)

        # Convert legacy format
        entries = []
        for symbol in data.get("portfolio", []):
            if isinstance(symbol, str):
                entries.append(WatchlistEntry(symbol=symbol, list_type="portfolio"))
            elif isinstance(symbol, dict):
                entries.append(WatchlistEntry(
                    symbol=symbol.get("symbol", ""),
                    list_type="portfolio",
                    triggers=symbol.get("triggers", []),
                ))

        for symbol in data.get("watchlist", []):
            if isinstance(symbol, str):
                entries.append(WatchlistEntry(symbol=symbol, list_type="watchlist"))
            elif isinstance(symbol, dict):
                entries.append(WatchlistEntry(
                    symbol=symbol.get("symbol", ""),
                    list_type="watchlist",
                    triggers=symbol.get("triggers", []),
                ))

        return cls(
            entries=entries,
            default_triggers=data.get("default_triggers", []),
        )

    def save_json(self, path: str) -> None:
        """Save watchlist to JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

