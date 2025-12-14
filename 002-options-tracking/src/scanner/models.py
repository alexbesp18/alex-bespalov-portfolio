"""Data models for stock options scanner."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class ConfigEntry(BaseModel):
    """Configuration entry for a stock options tracking task."""

    enabled: bool = Field(description="Whether this tracking task is enabled")
    ticker: str = Field(min_length=1, description="Stock ticker symbol")
    price: float = Field(gt=0, description="Strike price")
    type: Literal["Call", "Put"] = Field(description="Option type")
    month: str = Field(description="Expiration month")
    year: str = Field(description="Expiration year")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    strike: float = Field(default=0.0, ge=0, description="Strike price filter")
    otm_min: float = Field(default=0.0, ge=-100, le=1000, description="Minimum OTM percentage")
    otm_max: float = Field(default=100.0, ge=-100, le=1000, description="Maximum OTM percentage")
    open_interest: int = Field(default=0, ge=0, description="Minimum open interest filter")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is YYYY-MM-DD."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: str, info) -> str:
        """Validate end_date is after start_date."""
        if "start_date" in info.data:
            start_date = datetime.strptime(info.data["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(v, "%Y-%m-%d")
            if end_date <= start_date:
                raise ValueError("end_date must be after start_date")
        return v

    @field_validator("otm_max")
    @classmethod
    def validate_otm_range(cls, v: float, info) -> float:
        """Validate otm_max is greater than otm_min."""
        if "otm_min" in info.data:
            otm_min = info.data["otm_min"]
            if v <= otm_min:
                raise ValueError("otm_max must be greater than otm_min")
        return v


class Task(BaseModel):
    """Task for processing a specific options chain."""

    ticker: str = Field(min_length=1, description="Stock ticker symbol")
    date: str = Field(description="Expiration date in YYYY-MM-DD format")
    price: float = Field(gt=0, description="Current stock price")
    strike: float = Field(ge=0, description="Strike price filter")
    type: Literal["Call", "Put"] = Field(description="Option type")
    otm_min: float = Field(ge=-100, le=1000, description="Minimum OTM percentage")
    otm_max: float = Field(ge=-100, le=1000, description="Maximum OTM percentage")
    open_interest: int = Field(ge=0, description="Minimum open interest filter")

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is YYYY-MM-DD."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD")
        return v

    @field_validator("otm_max")
    @classmethod
    def validate_otm_range(cls, v: float, info) -> float:
        """Validate otm_max is greater than otm_min."""
        if "otm_min" in info.data:
            otm_min = info.data["otm_min"]
            if v <= otm_min:
                raise ValueError("otm_max must be greater than otm_min")
        return v

