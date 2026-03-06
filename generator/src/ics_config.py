"""Load and validate ICS configuration from config.toml."""

import tomllib
from typing import NotRequired, TypedDict


class IcsFileEntry(TypedDict):
    """ICS file entry with URL, filename, and team metadata.

    All team fields are required for proper UI display.
    """

    url: str
    filename: str
    team_name: str  # Full team name for calendar exports
    team_slug: str  # URL-safe identifier for web filtering (must be unique)
    team_display: str  # Short name for UI badges
    team_color: str  # Hex color for UI elements
    division: NotRequired[str]  # Optional: for documentation only


def load_ics_files() -> list[IcsFileEntry]:
    """Load and validate ICS URLs from config.toml.

    Returns:
        List of dicts with all required team metadata.

    Raises:
        FileNotFoundError: If config.toml doesn't exist.
        ValueError: If config.toml is missing required fields.
    """
    from paths import CONFIG_FILE

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

    with open(CONFIG_FILE, "rb") as f:
        config = tomllib.load(f)

    try:
        ics_files = config["ics"]["files"]
    except KeyError as e:
        raise ValueError(
            f"Config missing required key: {e}. "
            "Expected structure: [[ics.files]] with 'url' and 'filename' fields."
        ) from e

    # Validate each entry
    validated: list[IcsFileEntry] = []
    for i, entry in enumerate(ics_files):
        # Required fields
        required = [
            "url",
            "filename",
            "team_name",
            "team_slug",
            "team_display",
            "team_color",
        ]
        for field in required:
            if field not in entry:
                raise ValueError(f"Entry {i} missing required field '{field}'")

        if not entry["url"].startswith("http"):
            raise ValueError(f"Entry {i}: URL must start with http:// or https://")
        if not entry["filename"].endswith(".ics"):
            raise ValueError(f"Entry {i}: filename must end with .ics")

        # Validate hex color format
        color = entry["team_color"]
        if not color.startswith("#") or len(color) != 7:
            raise ValueError(
                f"Entry {i}: team_color must be a 7-character hex color like '#550f38'"
            )

        validated.append(entry)

    return validated
