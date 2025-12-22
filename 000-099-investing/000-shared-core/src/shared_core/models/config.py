"""
Scanner configuration models.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class OutputFormat(Enum):
    """Output format for scanner results."""
    TABLE = "table"
    JSON = "json"
    CSV = "csv"
    HTML = "html"


@dataclass
class ScanConfig:
    """
    Configuration for a scanner run.
    
    Attributes:
        tickers: List of ticker symbols to scan
        output_format: Output format (table, json, csv, html)
        limit: Maximum tickers to process
        dry_run: If True, don't send notifications
        verbose: Enable verbose logging
        cache_dir: Directory for cached data
        min_score: Minimum score threshold for signals
        max_results: Maximum results to return
        force_refresh: Force data refresh (ignore cache)
    """
    tickers: List[str] = field(default_factory=list)
    output_format: OutputFormat = OutputFormat.TABLE
    limit: Optional[int] = None
    dry_run: bool = False
    verbose: bool = False
    cache_dir: Optional[str] = None
    min_score: float = 0.0
    max_results: Optional[int] = None
    force_refresh: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tickers": self.tickers,
            "output_format": self.output_format.value,
            "limit": self.limit,
            "dry_run": self.dry_run,
            "verbose": self.verbose,
            "cache_dir": self.cache_dir,
            "min_score": self.min_score,
            "max_results": self.max_results,
            "force_refresh": self.force_refresh,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanConfig":
        """Create from dictionary."""
        output_format = data.get("output_format", "table")
        if isinstance(output_format, str):
            output_format = OutputFormat(output_format)

        return cls(
            tickers=data.get("tickers", []),
            output_format=output_format,
            limit=data.get("limit"),
            dry_run=data.get("dry_run", False),
            verbose=data.get("verbose", False),
            cache_dir=data.get("cache_dir"),
            min_score=data.get("min_score", 0.0),
            max_results=data.get("max_results"),
            force_refresh=data.get("force_refresh", False),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_args(cls, args) -> "ScanConfig":
        """Create from argparse namespace."""
        format_str = getattr(args, "format", "table") or "table"

        return cls(
            tickers=getattr(args, "tickers", []) or [],
            output_format=OutputFormat(format_str),
            limit=getattr(args, "limit", None),
            dry_run=getattr(args, "dry_run", False),
            verbose=getattr(args, "verbose", False),
            cache_dir=getattr(args, "cache_dir", None),
            min_score=getattr(args, "min_score", 0.0),
            max_results=getattr(args, "max_results", None),
            force_refresh=getattr(args, "force_refresh", False),
        )

