"""Load and validate ICS configuration from config.toml."""

import tomllib
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator

from central_f10.models import HEX_COLOR_PATTERN
from central_f10.paths import CONFIG_FILE


class IcsFileEntry(BaseModel):
    """ICS file entry with URL, filename, and team metadata.

    All team fields are required for proper UI display.
    """

    url: str
    filename: str
    team_name: str  # Full team name for calendar exports
    team_slug: str  # URL-safe identifier for web filtering (must be unique)
    team_display: str  # Short name for UI badges
    team_color: str  # Hex color for UI elements
    division: str | None = None  # Optional: for documentation only

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL uses http or https and has a valid host."""
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"URL must use http or https protocol, got '{v}'")
        if not parsed.netloc:
            raise ValueError(f"URL must have a valid host, got '{v}'")
        return v

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename ends with .ics."""
        if not v.endswith(".ics"):
            raise ValueError(f"filename must end with .ics, got '{v}'")
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


def load_ics_files(config_file: Path | None = None) -> list[IcsFileEntry]:
    """Load and validate ICS URLs from config.toml.

    Args:
        config_file: Path to config.toml. Defaults to CONFIG_FILE from paths module.

    Returns:
        List of IcsFileEntry instances with all required team metadata.

    Raises:
        FileNotFoundError: If config.toml doesn't exist.
        ValueError: If config.toml is missing required fields or has invalid entries.
    """
    config_path = config_file or CONFIG_FILE

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    try:
        ics_files = config["ics"]["files"]
    except KeyError as e:
        raise ValueError(
            f"Config missing required key: {e}. "
            "Expected structure: [[ics.files]] with 'url' and 'filename' fields."
        ) from e

    # Validate each entry via Pydantic model
    validated: list[IcsFileEntry] = []
    for i, entry in enumerate(ics_files):
        try:
            validated.append(IcsFileEntry.model_validate(entry))
        except Exception as e:
            raise ValueError(f"Entry {i}: {e}") from e

    return validated
