#!/usr/bin/env python3
"""Central F10 Schedule Generator - Main entry point.

Downloads ICS calendars from Profixio and generates:
- games.json: For the web app
- games.tsv: For Excel/Sheets import
- calendar.ics: For Google Calendar import
"""

import argparse
import logging
import sys
from pathlib import Path

from central_f10.data_importer import generate_all

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Central F10 Schedule Generator",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug-level logging",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all non-error output",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download and parse but don't write output files",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.toml (default: generator/config.toml)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the schedule generator pipeline.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_args(argv)

    # Configure logging level based on flags
    if args.quiet:
        level = logging.ERROR
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        logger.info("Starting schedule generation...")
        count = generate_all(
            config_path=args.config,
            dry_run=args.dry_run,
        )
        logger.info("Success! Generated schedule with %d games", count)
        return 0

    except FileNotFoundError as e:
        logger.error("File not found: %s", e)
        return 1
    except Exception as e:
        logger.error("Error during processing: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
