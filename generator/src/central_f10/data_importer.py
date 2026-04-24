"""Download ICS files and generate JSON, TSV, and ICS outputs."""

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests
from icalendar import Calendar, Event

from central_f10.config import IcsFileEntry, load_ics_files
from central_f10.models import GameEvent
from central_f10.paths import (
    CACHE_DIR,
    CALENDAR_ICS,
    GAMES_JSON,
    GAMES_TSV,
    ensure_dirs,
)

logger = logging.getLogger(__name__)

# HTTP request settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2
MAX_ICS_SIZE = 10 * 1024 * 1024  # 10MB limit

# Swedish timezone
SWEDISH_TZ = ZoneInfo("Europe/Stockholm")


def to_swedish_time(dt: datetime | None) -> datetime | None:
    """Convert UTC datetime to Swedish local time (CET/CEST).

    Args:
        dt: Datetime in UTC (must be timezone-aware).

    Returns:
        Datetime in Swedish timezone (CET/CEST).
    """
    if dt is None:
        return None
    # Ensure it's in UTC first, then convert to Swedish time
    if dt.tzinfo is None:
        logger.warning("Received naive datetime, assuming UTC: %s", dt)
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(SWEDISH_TZ)


def format_swedish_time(dt: datetime | None) -> str | None:
    """Convert UTC datetime to Swedish time and format as ISO string.

    Args:
        dt: Datetime in UTC (must be timezone-aware).

    Returns:
        ISO formatted string in Swedish timezone, or None if dt is None.
    """
    swedish = to_swedish_time(dt)
    return swedish.isoformat() if swedish else None


def download_ics_files(files: list[IcsFileEntry], save_dir: Path) -> dict[str, bool]:
    """Download ICS files with retry logic and validation.

    Args:
        files: List of ICS file entries with URL and filename.
        save_dir: Directory to save downloaded files.

    Returns:
        Dict mapping filename to success status.
    """
    save_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, bool] = {}

    for entry in files:
        url = entry.url
        filename = entry.filename
        file_path = save_dir / filename

        success = _download_with_retry(url, file_path)
        results[filename] = success

        if success:
            logger.info("Downloaded %s", filename)
        else:
            logger.error("Failed to download %s", filename)

    return results


def _download_with_retry(url: str, file_path: Path) -> bool:
    """Download a file with retry logic and content validation."""
    attempt = 0
    last_error: Exception | None = None

    while attempt < MAX_RETRIES:
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)

            if not response.ok:
                logger.warning(
                    "HTTP %d for %s (attempt %d/%d)",
                    response.status_code,
                    url,
                    attempt + 1,
                    MAX_RETRIES,
                )
                attempt += 1
                time.sleep(RETRY_BACKOFF**attempt)
                continue

            content = response.content

            if len(content) > MAX_ICS_SIZE:
                logger.error(
                    "ICS file too large: %d bytes (max %d) from %s",
                    len(content),
                    MAX_ICS_SIZE,
                    url,
                )
                return False

            if not _is_valid_ics_content(content):
                logger.error(
                    "Invalid ICS content from %s - received HTML or unexpected format",
                    url,
                )
                return False

            file_path.write_bytes(content)
            return True

        except requests.exceptions.Timeout as e:
            last_error = e
            logger.warning(
                "Timeout downloading %s (attempt %d/%d)",
                url,
                attempt + 1,
                MAX_RETRIES,
            )
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(
                "Request error for %s: %s (attempt %d/%d)",
                url,
                e,
                attempt + 1,
                MAX_RETRIES,
            )

        attempt += 1
        time.sleep(RETRY_BACKOFF**attempt)

    logger.error(
        "Failed to download %s after %d attempts: %s",
        url,
        MAX_RETRIES,
        last_error,
    )
    return False


def _is_valid_ics_content(content: bytes) -> bool:
    """Validate that content is valid ICS format."""
    try:
        text = content.decode("utf-8", errors="ignore").strip().lower()
        return text.startswith("begin:vcalendar") and "end:vcalendar" in text
    except UnicodeDecodeError:
        return False


def read_ical(ics_file: Path, entry: IcsFileEntry) -> list[GameEvent]:
    """Parse ICS file and return validated events.

    Args:
        ics_file: Path to ICS file.
        entry: ICS file entry with team metadata from config.

    Returns:
        List of validated GameEvent instances.
    """
    with open(ics_file, "rb") as f:
        cal = Calendar.from_ical(f.read())

    url_head = cal.get("URL")
    cal_url = url_head if url_head and len(url_head) > 0 else ""

    events: list[GameEvent] = []
    for comp in cal.walk():
        if comp.name != "VEVENT":
            continue

        dtstart = comp.get("DTSTART")
        dtend = comp.get("DTEND")

        # Use per-event URL if present, fall back to calendar-level URL
        event_url = str(comp.get("URL", "") or "").strip()
        url = event_url if event_url else cal_url

        raw_uid = str(comp.get("UID", "") or "").strip()
        gameid = raw_uid
        if not gameid:
            logger.warning("Skipping event with empty gameid in %s", ics_file.name)
            continue

        # Synthesize Cup Manager detail URLs when none is provided
        if not url and "@cupmanager.net" in raw_uid:
            year = dtstart.dt.year if dtstart else datetime.now().year
            gameid_for_url = raw_uid.split("-")[0]
            domain = urlparse(entry.url).netloc
            url = f"https://{domain}/{year}/result/match/{gameid_for_url}"

        raw_event = {
            "team": entry.team_name,
            "team_slug": entry.team_slug,
            "team_display": entry.team_display,
            "team_color": entry.team_color,
            "game": str(comp.get("SUMMARY", "") or "").strip(),
            "starttm": dtstart.dt if dtstart else None,
            "endtm": dtend.dt if dtend else None,
            "location": str(comp.get("LOCATION", "") or "").strip(),
            "gameid": gameid,
            "url": url,
        }

        try:
            validated = GameEvent.model_validate(raw_event)
            events.append(validated)
        except Exception as e:
            logger.warning("Skipping invalid event in %s: %s", ics_file.name, e)

    return events


def generate_json(events: list[GameEvent]) -> None:
    """Generate games.json for the web app.

    Times are converted to Swedish timezone (CET/CEST) for local display.
    """
    games_data = {
        "updated": datetime.now(tz=UTC).isoformat(),
        "timezone": "Europe/Stockholm",
        "games": [
            {
                "id": event.gameid,
                "team": event.team_slug,
                "teamDisplay": event.team_display,
                "teamFull": event.team,
                "teamColor": event.team_color,
                "game": event.game,
                "location": event.location,
                "start": format_swedish_time(event.starttm),
                "end": format_swedish_time(event.endtm),
                "url": event.url,
            }
            for event in events
        ],
    }

    GAMES_JSON.write_text(
        json.dumps(games_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("Generated %s (%d games)", GAMES_JSON, len(events))


def _escape_tsv(value: str) -> str:
    """Escape tabs and newlines in TSV field values."""
    return value.replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def generate_tsv(events: list[GameEvent]) -> None:
    """Generate games.tsv for Excel/Sheets import.

    Times are converted to Swedish timezone (CET/CEST) for local display.
    """
    lines = ["team\tgame\tlocation\tstart\tend\turl"]

    for event in events:
        start_local = to_swedish_time(event.starttm)
        end_local = to_swedish_time(event.endtm)
        start_str = start_local.strftime("%Y-%m-%d %H:%M") if start_local else ""
        end_str = end_local.strftime("%Y-%m-%d %H:%M") if end_local else ""
        lines.append(
            f"{_escape_tsv(event.team)}\t{_escape_tsv(event.game)}\t{_escape_tsv(event.location)}\t{start_str}\t{end_str}\t{_escape_tsv(event.url)}"
        )

    GAMES_TSV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Generated %s", GAMES_TSV)


def generate_ics(events: list[GameEvent]) -> None:
    """Generate combined calendar.ics for Google Calendar import."""
    cal = Calendar()
    cal.add("prodid", "-//Central F10 Basketball//central-f10//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("name", "Central F10 Matchschema")
    cal.add("description", "Basketball schedule for Central F10 teams")
    cal.add("x-publish-url", "https://basket.mtln.se/")

    for event in events:
        cal_event = Event()
        cal_event.add("uid", f"central-{event.gameid}")
        cal_event.add("dtstamp", datetime.now(tz=UTC))
        cal_event.add("summary", f"[{event.team}] {event.game}")
        cal_event.add("location", event.location)
        cal_event.add("dtstart", event.starttm)
        cal_event.add("dtend", event.endtm)
        if event.url:
            cal_event.add("url", event.url)
        cal.add_component(cal_event)

    CALENDAR_ICS.write_bytes(cal.to_ical())
    logger.info("Generated %s", CALENDAR_ICS)


def generate_all(
    *,
    config_path: Path | None = None,
    dry_run: bool = False,
) -> int:
    """Main function: download ICS files and generate all outputs.

    Args:
        config_path: Path to config.toml. Defaults to CONFIG_FILE.
        dry_run: If True, download and parse but don't write outputs.

    Returns:
        Number of events processed.

    Raises:
        RuntimeError: If no events were imported from any source.
    """
    ensure_dirs()

    # Load config (validates all required fields)
    files = load_ics_files(config_file=config_path)
    logger.info("Loading %d ICS sources from config", len(files))

    # Build filename -> metadata map
    team_meta: dict[str, IcsFileEntry] = {}
    config_filenames: set[str] = set()
    for entry in files:
        filename = entry.filename
        config_filenames.add(filename)
        team_meta[filename] = entry

    # Clean up stale cache files (not in current config)
    for cache_file in CACHE_DIR.glob("*.ics"):
        if cache_file.name not in config_filenames:
            logger.info("Removing stale cache file: %s", cache_file.name)
            cache_file.unlink()

    # Download files
    results = download_ics_files(files, CACHE_DIR)
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful

    if failed > 0:
        logger.warning("%d downloads failed, %d succeeded", failed, successful)

    if successful == 0:
        raise RuntimeError(
            "All ICS downloads failed. "
            "Check URLs in config.toml and network connectivity."
        )

    # Find and parse all .ics files
    ics_files = list(CACHE_DIR.glob("*.ics"))
    logger.info("Found %d ICS files to parse", len(ics_files))

    all_events: list[GameEvent] = []
    for ics_file in ics_files:
        meta = team_meta.get(ics_file.name)
        if not meta:
            logger.warning("No config metadata for %s, skipping", ics_file.name)
            continue

        events = read_ical(ics_file, entry=meta)
        all_events.extend(events)
        logger.info("Parsed %d events from %s", len(events), ics_file.name)

    if not all_events:
        raise RuntimeError("No events found in any ICS files.")

    # Sort once by start time
    sorted_events = sorted(all_events, key=lambda e: e.starttm)

    if dry_run:
        logger.info(
            "Dry run: skipping output generation (%d events)",
            len(sorted_events),
        )
        return len(sorted_events)

    # Generate outputs (already sorted)
    generate_json(sorted_events)
    generate_tsv(sorted_events)
    generate_ics(sorted_events)

    logger.info("Complete! Processed %d events", len(sorted_events))
    return len(sorted_events)
