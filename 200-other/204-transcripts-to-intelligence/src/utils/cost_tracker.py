"""
Cost Tracking and Budget Enforcement

Tracks LLM API costs and enforces budget limits.

Usage:
    from src.utils.cost_tracker import CostTracker, BudgetExceededError
    
    tracker = CostTracker(daily_budget=10.0)
    
    if not tracker.can_spend(0.50):
        raise BudgetExceededError("Daily budget exceeded")
    
    tracker.record_cost(0.50, video_id="abc123")
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any

__all__ = [
    "CostTracker",
    "CostRecord",
    "BudgetExceededError",
    "get_cost_tracker",
]

logger = logging.getLogger(__name__)


class BudgetExceededError(Exception):
    """Raised when spending would exceed budget."""
    
    def __init__(self, message: str, spent: float = 0, budget: float = 0):
        super().__init__(message)
        self.spent = spent
        self.budget = budget


@dataclass
class CostRecord:
    """A single cost record."""
    amount_usd: float
    timestamp: datetime
    video_id: Optional[str] = None
    operation: Optional[str] = None
    model: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount_usd": self.amount_usd,
            "timestamp": self.timestamp.isoformat(),
            "video_id": self.video_id,
            "operation": self.operation,
            "model": self.model,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostRecord":
        return cls(
            amount_usd=data["amount_usd"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            video_id=data.get("video_id"),
            operation=data.get("operation"),
            model=data.get("model"),
        )


class CostTracker:
    """Tracks LLM costs and enforces budgets.
    
    Features:
    - Daily budget enforcement
    - Per-video cost limits
    - Cost history persistence
    - Alert thresholds
    
    Example:
        >>> tracker = CostTracker(daily_budget=10.0)
        >>> tracker.record_cost(0.50, video_id="abc123")
        >>> print(f"Spent today: ${tracker.get_daily_total():.2f}")
        >>> if tracker.is_at_alert_threshold():
        ...     send_budget_alert()
    """
    
    DEFAULT_DAILY_BUDGET = 10.0
    DEFAULT_PER_VIDEO_LIMIT = 2.0
    DEFAULT_ALERT_THRESHOLD = 0.75  # Alert at 75% of budget
    
    def __init__(
        self,
        daily_budget: Optional[float] = None,
        per_video_limit: Optional[float] = None,
        alert_threshold: float = 0.75,
        persist_path: Optional[Path] = None,
        enforce_budget: bool = False,
    ):
        """Initialize cost tracker.
        
        Args:
            daily_budget: Maximum daily spend in USD.
            per_video_limit: Maximum cost per video in USD.
            alert_threshold: Alert when budget reaches this percentage.
            persist_path: Path to persist cost data.
            enforce_budget: If True, raise BudgetExceededError when exceeded.
        """
        self.daily_budget = daily_budget or self.DEFAULT_DAILY_BUDGET
        self.per_video_limit = per_video_limit or self.DEFAULT_PER_VIDEO_LIMIT
        self.alert_threshold = alert_threshold
        self.persist_path = persist_path
        self.enforce_budget = enforce_budget
        
        self._records: List[CostRecord] = []
        self._load_records()
    
    def _load_records(self) -> None:
        """Load persisted cost records."""
        if not self.persist_path or not self.persist_path.exists():
            return
        
        try:
            with open(self.persist_path) as f:
                data = json.load(f)
            
            self._records = [
                CostRecord.from_dict(r) for r in data.get("records", [])
            ]
            logger.debug(f"Loaded {len(self._records)} cost records")
        except Exception as e:
            logger.warning(f"Failed to load cost records: {e}")
    
    def _save_records(self) -> None:
        """Persist cost records."""
        if not self.persist_path:
            return
        
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "records": [r.to_dict() for r in self._records],
                "updated_at": datetime.now().isoformat(),
            }
            
            with open(self.persist_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cost records: {e}")
    
    def record_cost(
        self,
        amount_usd: float,
        video_id: Optional[str] = None,
        operation: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        """Record a cost.
        
        Args:
            amount_usd: Cost amount in USD.
            video_id: Associated video ID.
            operation: Operation type (e.g., "topic_extraction").
            model: Model used.
        """
        record = CostRecord(
            amount_usd=amount_usd,
            timestamp=datetime.now(),
            video_id=video_id,
            operation=operation,
            model=model,
        )
        
        self._records.append(record)
        self._save_records()
        
        logger.debug(
            f"Recorded cost: ${amount_usd:.4f} "
            f"(video={video_id}, operation={operation})"
        )
    
    def get_daily_total(self, target_date: Optional[date] = None) -> float:
        """Get total cost for a day.
        
        Args:
            target_date: Date to check (default: today).
            
        Returns:
            Total cost in USD.
        """
        target = target_date or date.today()
        
        daily_records = [
            r for r in self._records
            if r.timestamp.date() == target
        ]
        
        return sum(r.amount_usd for r in daily_records)
    
    def get_video_total(self, video_id: str) -> float:
        """Get total cost for a video.
        
        Args:
            video_id: Video ID to check.
            
        Returns:
            Total cost in USD.
        """
        video_records = [
            r for r in self._records
            if r.video_id == video_id
        ]
        
        return sum(r.amount_usd for r in video_records)
    
    def get_remaining_budget(self) -> float:
        """Get remaining daily budget.
        
        Returns:
            Remaining budget in USD.
        """
        return max(0, self.daily_budget - self.get_daily_total())
    
    def get_budget_percentage(self) -> float:
        """Get percentage of daily budget used.
        
        Returns:
            Percentage (0.0 to 1.0+).
        """
        if self.daily_budget <= 0:
            return 0.0
        return self.get_daily_total() / self.daily_budget
    
    def can_spend(self, amount: float) -> bool:
        """Check if spending amount is within budget.
        
        Args:
            amount: Amount to spend in USD.
            
        Returns:
            True if spending is allowed.
        """
        return self.get_remaining_budget() >= amount
    
    def check_budget(self, amount: float = 0) -> None:
        """Check budget and raise error if exceeded.
        
        Args:
            amount: Additional amount to spend.
            
        Raises:
            BudgetExceededError: If budget would be exceeded.
        """
        if not self.enforce_budget:
            return
        
        if not self.can_spend(amount):
            spent = self.get_daily_total()
            raise BudgetExceededError(
                f"Daily budget exceeded: ${spent:.2f} / ${self.daily_budget:.2f}",
                spent=spent,
                budget=self.daily_budget,
            )
    
    def check_video_limit(self, video_id: str, amount: float = 0) -> None:
        """Check per-video limit.
        
        Args:
            video_id: Video to check.
            amount: Additional amount to spend.
            
        Raises:
            BudgetExceededError: If video limit would be exceeded.
        """
        if not self.enforce_budget:
            return
        
        video_total = self.get_video_total(video_id)
        
        if video_total + amount > self.per_video_limit:
            raise BudgetExceededError(
                f"Per-video limit exceeded for {video_id}: "
                f"${video_total:.2f} / ${self.per_video_limit:.2f}",
                spent=video_total,
                budget=self.per_video_limit,
            )
    
    def is_at_alert_threshold(self) -> bool:
        """Check if spending is at alert threshold.
        
        Returns:
            True if at or above alert threshold.
        """
        return self.get_budget_percentage() >= self.alert_threshold
    
    def get_alert_message(self) -> Optional[str]:
        """Get alert message if at threshold.
        
        Returns:
            Alert message or None.
        """
        percentage = self.get_budget_percentage()
        spent = self.get_daily_total()
        
        if percentage >= 1.0:
            return (
                f"🚨 Daily budget exceeded: ${spent:.2f} / ${self.daily_budget:.2f} "
                f"({percentage:.0%})"
            )
        elif percentage >= 0.9:
            return (
                f"⚠️ Daily budget at 90%: ${spent:.2f} / ${self.daily_budget:.2f}"
            )
        elif percentage >= self.alert_threshold:
            return (
                f"📊 Daily budget at {percentage:.0%}: "
                f"${spent:.2f} / ${self.daily_budget:.2f}"
            )
        
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary.
        
        Returns:
            Summary dict with totals and stats.
        """
        today = date.today()
        daily_total = self.get_daily_total()
        
        return {
            "daily_total_usd": daily_total,
            "daily_budget_usd": self.daily_budget,
            "remaining_usd": self.get_remaining_budget(),
            "budget_percentage": self.get_budget_percentage(),
            "at_alert_threshold": self.is_at_alert_threshold(),
            "records_today": len([
                r for r in self._records
                if r.timestamp.date() == today
            ]),
            "total_records": len(self._records),
        }


# Global tracker instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker(
    daily_budget: Optional[float] = None,
    persist_path: Optional[Path] = None,
) -> CostTracker:
    """Get or create global cost tracker.
    
    Args:
        daily_budget: Daily budget (only used on first call).
        persist_path: Path to persist data (only used on first call).
        
    Returns:
        CostTracker instance.
    """
    global _cost_tracker
    
    if _cost_tracker is None:
        _cost_tracker = CostTracker(
            daily_budget=daily_budget,
            persist_path=persist_path or Path("data/.cost_tracker.json"),
        )
    
    return _cost_tracker

