"""Path constants for the schedule generator."""

from pathlib import Path

# Generator directory (where this file lives)
GENERATOR_DIR = Path(__file__).parent.parent.parent

# Project root (Pages repo root)
PROJECT_ROOT = GENERATOR_DIR.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = GENERATOR_DIR / "cache"

# Output files
GAMES_JSON = DATA_DIR / "games.json"
GAMES_TSV = DATA_DIR / "games.tsv"
CALENDAR_ICS = DATA_DIR / "calendar.ics"

# Config
CONFIG_FILE = GENERATOR_DIR / "config.toml"


def ensure_dirs() -> None:
    """Create output and cache directories if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
