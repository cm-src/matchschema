"""Pydantic models for data validation."""

import re
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

# Hex color pattern: # followed by exactly 6 hex characters
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


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
        if not HEX_COLOR_PATTERN.match(v):
            raise ValueError(
                f"team_color must be a valid hex color like '#550f38', got '{v}'"
            )
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL is http or https."""
        if not v:
            return v
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"URL must use http or https protocol, got '{v}'")
        if not parsed.netloc:
            raise ValueError(f"URL must have a valid host, got '{v}'")
        return v

    @field_validator("endtm")
    @classmethod
    def end_after_start(cls, v: datetime, info: ValidationInfo) -> datetime:
        """Validate that end time is after start time."""
        starttm = info.data.get("starttm")
        if starttm and v < starttm:
            raise ValueError(f"endtm ({v}) must be after starttm ({starttm})")
        return v
