#!/usr/bin/env python3
"""Central F10 Schedule Generator - Main entry point.

Downloads ICS calendars from Profixio and generates:
- games.json: For the web app
- games.tsv: For Excel/Sheets import
- calendar.ics: For Google Calendar import
"""

import logging
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_importer import generate_all  # type: ignore[import-not-found]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Run the schedule generator pipeline.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        logger.info("Starting schedule generation...")
        count = generate_all()
        logger.info("Success! Generated schedule with %d games", count)
        return 0

    except FileNotFoundError as e:
        logger.error("File not found: %s", e)
        return 1
    except Exception as e:
        logger.error("Error during processing: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
