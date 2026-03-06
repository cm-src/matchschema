"""Shared pytest fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Path:
    """Isolated temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_ics_content() -> bytes:
    """Valid ICS file content for testing."""
    return b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Profixio//EN
NAME:Central F10 Vinrod - Flickor U16
BEGIN:VEVENT
UID:pro-mce-test123
DTSTART:20250315T140000Z
DTEND:20250315T160000Z
SUMMARY:Central F10 Vinrod vs Opponent
LOCATION:Sports Hall Arena
URL:https://profixio.com/game/123
END:VEVENT
END:VCALENDAR
"""


@pytest.fixture
def sample_html_content() -> bytes:
    """Invalid HTML content (not ICS) for testing."""
    return b"""<!DOCTYPE html>
<html>
<head><title>Error</title></head>
<body><h1>403 Forbidden</h1></body>
</html>
"""


@pytest.fixture
def valid_config_toml() -> str:
    """Valid config.toml content for testing."""
    return """
[ics]
[[ics.files]]
url = "https://profixio.com/calendar1.ics"
filename = "team1.ics"
team_name = "Central F10 Vinröd"
team_slug = "vinrod"
team_display = "Vinröd"
team_color = "#550f38"

[[ics.files]]
url = "https://profixio.com/calendar2.ics"
filename = "team2.ics"
team_name = "Central F10 Gul"
team_slug = "gul"
team_display = "Gul"
team_color = "#fec225"
"""


@pytest.fixture
def minimal_team_meta() -> dict:
    """Minimal team metadata for testing read_ical."""
    return {
        "team_name": "Central F10 Vinröd",
        "team_slug": "vinrod",
        "team_display": "Vinröd",
        "team_color": "#550f38",
    }
