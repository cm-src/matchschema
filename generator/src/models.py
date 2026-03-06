"""Pydantic models for data validation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class GameEvent(BaseModel):
    """Validated game event from ICS calendar."""

    team: str  # Full team name
    game: str
    starttm: datetime
    endtm: datetime
    location: str
    gameid: str
    url: str
    team_slug: str  # URL-safe identifier for filtering
    team_display: str  # Short name for UI badges
    team_color: str  # Hex color for UI styling

    @field_validator(
        "team",
        "game",
        "location",
        "gameid",
        "url",
        "team_slug",
        "team_display",
        "team_color",
    )
    @classmethod
    def strip_strings(cls, v: str) -> str:
        """Strip whitespace from string fields."""
        return v.strip() if v else ""

    @field_validator("team_color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate hex color format."""
        if not v.startswith("#") or len(v) != 7:
            raise ValueError(f"team_color must be a 7-character hex color, got '{v}'")
        return v

    @field_validator("endtm")
    @classmethod
    def end_after_start(cls, v: datetime, info: Any) -> datetime:
        """Validate that end time is after start time."""
        starttm = info.data.get("starttm")
        if starttm and v < starttm:
            raise ValueError(f"endtm ({v}) must be after starttm ({starttm})")
        return v


def validate_event(event: dict[str, Any]) -> GameEvent:
    """Validate a raw event dict and return a GameEvent.

    Args:
        event: Raw event dict from ICS parsing.

    Returns:
        Validated GameEvent instance.

    Raises:
        ValueError: If event data is invalid.
    """
    return GameEvent.model_validate(event)
