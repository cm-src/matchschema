"""Pydantic models for data validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from central_f10.validation import (
    HEX_COLOR_PATTERN,  # re-exported for backward compatibility
    validate_hex_color,
    validate_http_url,
)

__all__ = ["HEX_COLOR_PATTERN", "GameEvent"]


class GameEvent(BaseModel):
    """Validated game event from ICS calendar."""

    model_config = ConfigDict(extra="forbid")

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
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("team_color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate hex color format."""
        return validate_hex_color(v)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL is http or https (empty allowed)."""
        return validate_http_url(v, allow_empty=True)

    @field_validator("endtm")
    @classmethod
    def end_after_start(cls, v: datetime, info: ValidationInfo) -> datetime:
        """Validate that end time is after start time."""
        starttm = info.data.get("starttm")
        if starttm and v < starttm:
            raise ValueError(f"endtm ({v}) must be after starttm ({starttm})")
        return v
