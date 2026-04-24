"""Unit tests for the data import pipeline."""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from central_f10.config import IcsFileEntry
from central_f10.data_importer import (
    MAX_RETRIES,
    GameEvent,
    _download_with_retry,
    download_ics_files,
    format_swedish_time,
    generate_all,
    generate_ics,
    generate_json,
    generate_tsv,
    read_ical,
    to_swedish_time,
)


def _make_event(
    team: str = "Central F10",
    game: str = "Game 1",
    starttm: datetime = datetime(2025, 3, 15, 14, 0, tzinfo=UTC),
    endtm: datetime = datetime(2025, 3, 15, 16, 0, tzinfo=UTC),
    location: str = "Arena",
    gameid: str = "test123",
    url: str = "https://example.com/game",
    team_slug: str = "team",
    team_display: str = "Team",
    team_color: str = "#550f38",
) -> GameEvent:
    """Create a GameEvent with sensible defaults for tests."""
    return GameEvent(
        team=team,
        game=game,
        starttm=starttm,
        endtm=endtm,
        location=location,
        gameid=gameid,
        url=url,
        team_slug=team_slug,
        team_display=team_display,
        team_color=team_color,
    )


def _make_entry(**overrides: object) -> IcsFileEntry:
    """Create an IcsFileEntry with sensible defaults for tests."""
    defaults: dict[str, object] = {
        "url": "https://profixio.com/calendar.ics",
        "filename": "test.ics",
        "team_name": "Central F10 Vinröd",
        "team_slug": "vinrod",
        "team_display": "Vinröd",
        "team_color": "#550f38",
    }
    defaults.update(overrides)
    return IcsFileEntry(**defaults)  # ty: ignore[invalid-argument-type]


# ---------------------------------------------------------------------------
# to_swedish_time / format_swedish_time
# ---------------------------------------------------------------------------


class TestToSwedishTime:
    """Tests for to_swedish_time function."""

    def test_utc_winter_time(self) -> None:
        """UTC winter time (CET = UTC+1) converts correctly."""
        dt = datetime(2025, 1, 15, 14, 0, tzinfo=UTC)
        result = to_swedish_time(dt)
        assert result is not None
        assert result.hour == 15  # 14:00 UTC = 15:00 CET
        assert result.tzinfo is not None
        assert result.tzinfo.key == "Europe/Stockholm"  # ty: ignore[unresolved-attribute]

    def test_utc_summer_time(self) -> None:
        """UTC summer time (CEST = UTC+2) converts correctly."""
        dt = datetime(2025, 7, 15, 14, 0, tzinfo=UTC)
        result = to_swedish_time(dt)
        assert result is not None
        assert result.hour == 16  # 14:00 UTC = 16:00 CEST

    def test_naive_datetime_assumes_utc(self) -> None:
        """Naive datetime is treated as UTC with a warning log."""
        dt = datetime(2025, 1, 15, 14, 0)  # naive
        with patch("central_f10.data_importer.logger") as mock_logger:
            result = to_swedish_time(dt)
            mock_logger.warning.assert_called_once()
            assert "naive datetime" in mock_logger.warning.call_args[0][0].lower()
        assert result is not None
        assert result.hour == 15

    def test_none_input(self) -> None:
        """None input returns None."""
        assert to_swedish_time(None) is None

    def test_preserves_date(self) -> None:
        """Conversion preserves year, month, day."""
        dt = datetime(2025, 6, 1, 23, 30, tzinfo=UTC)
        result = to_swedish_time(dt)
        assert result is not None
        # 23:30 UTC in summer = 01:30 CEST next day
        assert result.day == 2
        assert result.month == 6


class TestFormatSwedishTime:
    """Tests for format_swedish_time function."""

    def test_iso_format_output(self) -> None:
        """Output is ISO-formatted string in Swedish timezone."""
        dt = datetime(2025, 1, 15, 14, 0, tzinfo=UTC)
        result = format_swedish_time(dt)
        assert result is not None
        assert "15:00" in result
        assert result.startswith("2025-01-15")

    def test_none_input(self) -> None:
        """None input returns None."""
        assert format_swedish_time(None) is None


# ---------------------------------------------------------------------------
# download_ics_files / _download_with_retry
# ---------------------------------------------------------------------------


class TestDownloadWithRetry:
    """Tests for _download_with_retry function."""

    def test_success(self, temp_dir: Path) -> None:
        """Successful download returns True and writes file."""
        file_path = temp_dir / "test.ics"
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"

        with patch(
            "central_f10.data_importer.requests.get",
            return_value=mock_response,
        ):
            assert (
                _download_with_retry("https://example.com/test.ics", file_path) is True
            )

        assert file_path.exists()
        assert file_path.read_bytes() == b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"

    def test_http_error_retries(self, temp_dir: Path) -> None:
        """HTTP error triggers retries; fails after MAX_RETRIES."""
        file_path = temp_dir / "test.ics"
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500

        with (
            patch(
                "central_f10.data_importer.requests.get",
                return_value=mock_response,
            ),
            patch("central_f10.data_importer.time.sleep"),
        ):
            assert (
                _download_with_retry("https://example.com/test.ics", file_path) is False
            )

        assert not file_path.exists()

    def test_timeout_retries(self, temp_dir: Path) -> None:
        """Timeout triggers retries; fails after MAX_RETRIES."""
        file_path = temp_dir / "test.ics"

        with (
            patch(
                "central_f10.data_importer.requests.get",
                side_effect=requests.exceptions.Timeout("timed out"),
            ),
            patch("central_f10.data_importer.time.sleep"),
        ):
            assert (
                _download_with_retry("https://example.com/test.ics", file_path) is False
            )

    def test_request_exception_retries(self, temp_dir: Path) -> None:
        """Generic RequestException triggers retries; fails after MAX_RETRIES."""
        file_path = temp_dir / "test.ics"

        with (
            patch(
                "central_f10.data_importer.requests.get",
                side_effect=requests.exceptions.ConnectionError("connection failed"),
            ),
            patch("central_f10.data_importer.time.sleep"),
        ):
            assert (
                _download_with_retry("https://example.com/test.ics", file_path) is False
            )

    def test_oversized_file_rejected(self, temp_dir: Path) -> None:
        """File exceeding MAX_ICS_SIZE is rejected immediately."""
        file_path = temp_dir / "test.ics"
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = b"x" * (10 * 1024 * 1024 + 1)  # Just over 10MB

        with patch(
            "central_f10.data_importer.requests.get",
            return_value=mock_response,
        ):
            assert (
                _download_with_retry("https://example.com/test.ics", file_path) is False
            )

    def test_invalid_ics_content_rejected(self, temp_dir: Path) -> None:
        """Non-ICS content (e.g. HTML) is rejected."""
        file_path = temp_dir / "test.ics"
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = b"<html><body>403 Forbidden</body></html>"

        with patch(
            "central_f10.data_importer.requests.get",
            return_value=mock_response,
        ):
            assert (
                _download_with_retry("https://example.com/test.ics", file_path) is False
            )

    def test_retry_count_matches_max_retries(self, temp_dir: Path) -> None:
        """Exactly MAX_RETRIES requests are made on persistent failure."""
        file_path = temp_dir / "test.ics"
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 503

        with (
            patch(
                "central_f10.data_importer.requests.get",
                return_value=mock_response,
            ) as mock_get,
            patch("central_f10.data_importer.time.sleep"),
        ):
            _download_with_retry("https://example.com/test.ics", file_path)

        assert mock_get.call_count == MAX_RETRIES


class TestDownloadIcsFiles:
    """Tests for download_ics_files function."""

    def test_all_success(self, temp_dir: Path) -> None:
        """All successful downloads reported correctly."""
        entries = [
            IcsFileEntry(
                url="https://example.com/a.ics",
                filename="a.ics",
                team_name="Team A",
                team_slug="a",
                team_display="A",
                team_color="#550f38",
            ),
            IcsFileEntry(
                url="https://example.com/b.ics",
                filename="b.ics",
                team_name="Team B",
                team_slug="b",
                team_display="B",
                team_color="#fec225",
            ),
        ]

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"

        with patch(
            "central_f10.data_importer.requests.get",
            return_value=mock_response,
        ):
            results = download_ics_files(entries, temp_dir)

        assert results == {"a.ics": True, "b.ics": True}

    def test_partial_failure(self, temp_dir: Path) -> None:
        """Partial failures reported correctly."""
        entries = [
            IcsFileEntry(
                url="https://example.com/good.ics",
                filename="good.ics",
                team_name="Good",
                team_slug="good",
                team_display="Good",
                team_color="#550f38",
            ),
            IcsFileEntry(
                url="https://example.com/bad.ics",
                filename="bad.ics",
                team_name="Bad",
                team_slug="bad",
                team_display="Bad",
                team_color="#fec225",
            ),
        ]

        mock_response_ok = MagicMock()
        mock_response_ok.ok = True
        mock_response_ok.content = b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"

        mock_response_fail = MagicMock()
        mock_response_fail.ok = False
        mock_response_fail.status_code = 404

        with (
            patch(
                "central_f10.data_importer.requests.get",
                side_effect=[
                    mock_response_ok,
                    mock_response_fail,
                ]
                + [mock_response_fail] * MAX_RETRIES,
            ),
            patch("central_f10.data_importer.time.sleep"),
        ):
            results = download_ics_files(entries, temp_dir)

        assert results["good.ics"] is True
        assert results["bad.ics"] is False

    def test_creates_save_dir(self, temp_dir: Path) -> None:
        """download_ics_files creates the save directory if missing."""
        save_dir = temp_dir / "new_dir"
        entries: list[IcsFileEntry] = []

        download_ics_files(entries, save_dir)

        assert save_dir.exists()


# ---------------------------------------------------------------------------
# read_ical
# ---------------------------------------------------------------------------


class TestReadIcal:
    """Tests for read_ical function."""

    def test_parses_events(
        self,
        temp_dir: Path,
        sample_ics_content: bytes,
        minimal_team_meta: dict,
    ) -> None:
        """read_ical correctly parses ICS content."""
        ics_file = temp_dir / "test.ics"
        ics_file.write_bytes(sample_ics_content)

        entry = IcsFileEntry(
            url="https://profixio.com/calendar.ics",
            filename="test.ics",
            **minimal_team_meta,
        )
        events = read_ical(ics_file, entry=entry)

        assert len(events) == 1
        event = events[0]
        assert event.team == "Central F10 Vinröd"
        assert "Central F10 Vinrod vs Opponent" in event.game
        assert event.location == "Sports Hall Arena"
        assert event.gameid == "test123"
        assert event.team_slug == "vinrod"
        assert event.team_display == "Vinröd"
        assert event.team_color == "#550f38"

    def test_team_name_from_config(
        self, temp_dir: Path, sample_ics_content: bytes
    ) -> None:
        """read_ical uses team_name from config, not ICS."""
        ics_file = temp_dir / "test.ics"
        ics_file.write_bytes(sample_ics_content)

        entry = IcsFileEntry(
            url="https://profixio.com/calendar.ics",
            filename="test.ics",
            team_name="Custom Team Name",
            team_slug="custom",
            team_display="Custom",
            team_color="#000000",
        )
        events = read_ical(ics_file, entry=entry)

        assert len(events) == 1
        assert events[0].team == "Custom Team Name"
        assert events[0].team_slug == "custom"

    def test_strips_pro_mce_prefix_from_uid(
        self,
        temp_dir: Path,
        sample_ics_content: bytes,
        minimal_team_meta: dict,
    ) -> None:
        """read_ical strips 'pro-mce-' prefix from gameid."""
        ics_file = temp_dir / "test.ics"
        ics_file.write_bytes(sample_ics_content)

        entry = IcsFileEntry(
            url="https://profixio.com/calendar.ics",
            filename="test.ics",
            **minimal_team_meta,
        )
        events = read_ical(ics_file, entry=entry)

        assert events[0].gameid == "test123"  # "pro-mce-test123" -> "test123"

    def test_skips_invalid_events(
        self, temp_dir: Path, minimal_team_meta: dict
    ) -> None:
        """read_ical skips events that fail GameEvent validation."""
        # ICS with an event missing DTEND (will fail GameEvent required-field check)
        ics_content = b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
UID:pro-mce-bad1
DTSTART:20250315T140000Z
SUMMARY:Game Without End
LOCATION:Some Arena
END:VEVENT
END:VCALENDAR
"""
        ics_file = temp_dir / "test.ics"
        ics_file.write_bytes(ics_content)

        entry = IcsFileEntry(
            url="https://profixio.com/calendar.ics",
            filename="test.ics",
            **minimal_team_meta,
        )
        with patch("central_f10.data_importer.logger") as mock_logger:
            events = read_ical(ics_file, entry=entry)
            mock_logger.warning.assert_called()

        assert len(events) == 0

    def test_multiple_events(self, temp_dir: Path, minimal_team_meta: dict) -> None:
        """read_ical parses multiple VEVENT entries."""
        ics_content = b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
UID:pro-mce-evt1
DTSTART:20250315T140000Z
DTEND:20250315T160000Z
SUMMARY:Game 1
LOCATION:Arena 1
URL:https://example.com/1
END:VEVENT
BEGIN:VEVENT
UID:pro-mce-evt2
DTSTART:20250316T140000Z
DTEND:20250316T160000Z
SUMMARY:Game 2
LOCATION:Arena 2
URL:https://example.com/2
END:VEVENT
END:VCALENDAR
"""
        ics_file = temp_dir / "test.ics"
        ics_file.write_bytes(ics_content)

        entry = IcsFileEntry(
            url="https://profixio.com/calendar.ics",
            filename="test.ics",
            **minimal_team_meta,
        )
        events = read_ical(ics_file, entry=entry)

        assert len(events) == 2

    def test_no_events_in_calendar(
        self, temp_dir: Path, minimal_team_meta: dict
    ) -> None:
        """read_ical returns empty list for ICS with no VEVENT entries."""
        ics_content = b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
END:VCALENDAR
"""
        ics_file = temp_dir / "test.ics"
        ics_file.write_bytes(ics_content)

        entry = IcsFileEntry(
            url="https://profixio.com/calendar.ics",
            filename="test.ics",
            **minimal_team_meta,
        )
        events = read_ical(ics_file, entry=entry)

        assert len(events) == 0

    def test_uses_calendar_url_as_fallback(
        self, temp_dir: Path, minimal_team_meta: dict
    ) -> None:
        """read_ical falls back to calendar-level URL when event has no URL."""
        ics_content = b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
URL:https://profixio.com/calendar
BEGIN:VEVENT
UID:pro-mce-nourl
DTSTART:20250315T140000Z
DTEND:20250315T160000Z
SUMMARY:Game No URL
LOCATION:Arena
END:VEVENT
END:VCALENDAR
"""
        ics_file = temp_dir / "test.ics"
        ics_file.write_bytes(ics_content)

        entry = IcsFileEntry(
            url="https://profixio.com/calendar.ics",
            filename="test.ics",
            **minimal_team_meta,
        )
        events = read_ical(ics_file, entry=entry)

        assert len(events) == 1
        assert events[0].url == "https://profixio.com/calendar"


# ---------------------------------------------------------------------------
# generate_json / generate_tsv / generate_ics
# ---------------------------------------------------------------------------


class TestGenerateJson:
    """Tests for generate_json function."""

    def test_structure(self, temp_dir: Path) -> None:
        """Generated JSON has correct top-level structure."""
        output_file = temp_dir / "games.json"
        with patch("central_f10.data_importer.GAMES_JSON", output_file):
            generate_json([_make_event()])

        data = json.loads(output_file.read_text())
        assert "updated" in data
        assert "timezone" in data
        assert data["timezone"] == "Europe/Stockholm"
        assert "games" in data
        assert len(data["games"]) == 1

    def test_game_fields(self, temp_dir: Path) -> None:
        """Each game entry has the expected fields."""
        output_file = temp_dir / "games.json"
        with patch("central_f10.data_importer.GAMES_JSON", output_file):
            generate_json([_make_event()])

        data = json.loads(output_file.read_text())
        game = data["games"][0]
        expected_keys = {
            "id",
            "team",
            "teamDisplay",
            "teamFull",
            "teamColor",
            "game",
            "location",
            "start",
            "end",
            "url",
        }
        assert set(game.keys()) == expected_keys

    def test_swedish_time_in_output(self, temp_dir: Path) -> None:
        """Start/end times are in Swedish timezone format."""
        output_file = temp_dir / "games.json"
        event = _make_event(starttm=datetime(2025, 1, 15, 14, 0, tzinfo=UTC))
        with patch("central_f10.data_importer.GAMES_JSON", output_file):
            generate_json([event])

        data = json.loads(output_file.read_text())
        # 14:00 UTC in January = 15:00 CET
        assert "15:00" in data["games"][0]["start"]

    def test_events_preserve_order(self, temp_dir: Path) -> None:
        """Events are emitted in the order received (sorted by generate_all)."""
        output_file = temp_dir / "games.json"
        # Already sorted (generate_all sorts before calling generate_json)
        events = [
            _make_event(
                gameid="early",
                starttm=datetime(2025, 3, 10, 14, 0, tzinfo=UTC),
                endtm=datetime(2025, 3, 10, 16, 0, tzinfo=UTC),
            ),
            _make_event(
                gameid="late",
                starttm=datetime(2025, 3, 20, 14, 0, tzinfo=UTC),
                endtm=datetime(2025, 3, 20, 16, 0, tzinfo=UTC),
            ),
        ]
        with patch("central_f10.data_importer.GAMES_JSON", output_file):
            generate_json(events)

        data = json.loads(output_file.read_text())
        assert data["games"][0]["id"] == "early"
        assert data["games"][1]["id"] == "late"

    def test_empty_events(self, temp_dir: Path) -> None:
        """Empty events list produces valid JSON with empty games array."""
        output_file = temp_dir / "games.json"
        with patch("central_f10.data_importer.GAMES_JSON", output_file):
            generate_json([])

        data = json.loads(output_file.read_text())
        assert data["games"] == []


class TestGenerateTsv:
    """Tests for generate_tsv function."""

    def test_header_and_data(self, temp_dir: Path) -> None:
        """TSV has correct header and data rows."""
        output_file = temp_dir / "games.tsv"
        with patch("central_f10.data_importer.GAMES_TSV", output_file):
            generate_tsv([_make_event()])

        lines = output_file.read_text().strip().split("\n")
        assert lines[0] == "team\tgame\tlocation\tstart\tend\turl"
        assert len(lines) == 2  # header + 1 data row

    def test_swedish_time_format(self, temp_dir: Path) -> None:
        """TSV times are formatted as YYYY-MM-DD HH:MM in Swedish timezone."""
        output_file = temp_dir / "games.tsv"
        event = _make_event(starttm=datetime(2025, 1, 15, 14, 0, tzinfo=UTC))
        with patch("central_f10.data_importer.GAMES_TSV", output_file):
            generate_tsv([event])

        lines = output_file.read_text().strip().split("\n")
        # 14:00 UTC in January = 15:00 CET
        assert "2025-01-15 15:00" in lines[1]

    def test_escapes_tabs_in_fields(self, temp_dir: Path) -> None:
        """Tabs and newlines in field values are escaped."""
        output_file = temp_dir / "games.tsv"
        event = _make_event(location="Arena\tMain\tHall")
        with patch("central_f10.data_importer.GAMES_TSV", output_file):
            generate_tsv([event])

        lines = output_file.read_text().strip().split("\n")
        assert "\\t" in lines[1]  # Literal tabs escaped as \t

    def test_multiple_events(self, temp_dir: Path) -> None:
        """Multiple events produce multiple data rows."""
        output_file = temp_dir / "games.tsv"
        events = [
            _make_event(gameid="a"),
            _make_event(gameid="b"),
        ]
        with patch("central_f10.data_importer.GAMES_TSV", output_file):
            generate_tsv(events)

        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 3  # header + 2 data rows


class TestGenerateIcs:
    """Tests for generate_ics function."""

    def test_structure(self, temp_dir: Path) -> None:
        """Generated ICS has correct structure."""
        output_file = temp_dir / "calendar.ics"
        with patch("central_f10.data_importer.CALENDAR_ICS", output_file):
            generate_ics([_make_event()])

        assert output_file.exists()
        content = output_file.read_text()
        assert "BEGIN:VCALENDAR" in content
        assert "BEGIN:VEVENT" in content
        assert "CALSCALE:GREGORIAN" in content
        assert "METHOD:PUBLISH" in content
        assert "DTSTAMP" in content

    def test_team_in_summary(self, temp_dir: Path) -> None:
        """ICS event summary includes team name."""
        output_file = temp_dir / "calendar.ics"
        with patch("central_f10.data_importer.CALENDAR_ICS", output_file):
            generate_ics([_make_event(team="Central F10 Vinrod")])

        content = output_file.read_text()
        assert "[Central F10 Vinrod]" in content

    def test_uid_prefix(self, temp_dir: Path) -> None:
        """ICS event UIDs have 'central-' prefix."""
        output_file = temp_dir / "calendar.ics"
        with patch("central_f10.data_importer.CALENDAR_ICS", output_file):
            generate_ics([_make_event(gameid="abc123")])

        content = output_file.read_text()
        assert "central-abc123" in content

    def test_url_included(self, temp_dir: Path) -> None:
        """ICS event includes URL property when present."""
        output_file = temp_dir / "calendar.ics"
        with patch("central_f10.data_importer.CALENDAR_ICS", output_file):
            generate_ics([_make_event(url="https://profixio.com/game/123")])

        content = output_file.read_text()
        assert "https://profixio.com/game/123" in content

    def test_multiple_events(self, temp_dir: Path) -> None:
        """Multiple events produce multiple VEVENT blocks."""
        output_file = temp_dir / "calendar.ics"
        events = [
            _make_event(gameid="a", game="Game A"),
            _make_event(gameid="b", game="Game B"),
        ]
        with patch("central_f10.data_importer.CALENDAR_ICS", output_file):
            generate_ics(events)

        content = output_file.read_text()
        assert content.count("BEGIN:VEVENT") == 2


# ---------------------------------------------------------------------------
# generate_all (pipeline)
# ---------------------------------------------------------------------------


class TestGenerateAll:
    """Tests for generate_all pipeline function."""

    def test_success(
        self,
        temp_dir: Path,
        sample_ics_content: bytes,
        valid_config_toml: str,
    ) -> None:
        """Successful pipeline returns event count."""
        config_file = temp_dir / "config.toml"
        config_file.write_text(valid_config_toml)

        cache_dir = temp_dir / "cache"
        cache_dir.mkdir()
        data_dir = temp_dir / "data"
        data_dir.mkdir()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = sample_ics_content

        with (
            patch("central_f10.data_importer.CACHE_DIR", cache_dir),
            patch(
                "central_f10.data_importer.GAMES_JSON",
                data_dir / "games.json",
            ),
            patch(
                "central_f10.data_importer.GAMES_TSV",
                data_dir / "games.tsv",
            ),
            patch(
                "central_f10.data_importer.CALENDAR_ICS",
                data_dir / "calendar.ics",
            ),
            patch(
                "central_f10.data_importer.requests.get",
                return_value=mock_response,
            ),
            patch("central_f10.data_importer.ensure_dirs"),
        ):
            count = generate_all(config_path=config_file)

        assert count > 0
        assert (data_dir / "games.json").exists()
        assert (data_dir / "games.tsv").exists()
        assert (data_dir / "calendar.ics").exists()

    def test_all_downloads_fail_raises_runtime_error(
        self, temp_dir: Path, valid_config_toml: str
    ) -> None:
        """RuntimeError raised when all downloads fail."""
        config_file = temp_dir / "config.toml"
        config_file.write_text(valid_config_toml)
        cache_dir = temp_dir / "cache"
        cache_dir.mkdir()
        data_dir = temp_dir / "data"
        data_dir.mkdir()

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500

        with (
            patch("central_f10.data_importer.CACHE_DIR", cache_dir),
            patch(
                "central_f10.data_importer.GAMES_JSON",
                data_dir / "games.json",
            ),
            patch(
                "central_f10.data_importer.GAMES_TSV",
                data_dir / "games.tsv",
            ),
            patch(
                "central_f10.data_importer.CALENDAR_ICS",
                data_dir / "calendar.ics",
            ),
            patch(
                "central_f10.data_importer.requests.get",
                return_value=mock_response,
            ),
            patch("central_f10.data_importer.time.sleep"),
            patch("central_f10.data_importer.ensure_dirs"),
            pytest.raises(RuntimeError, match="All ICS downloads failed"),
        ):
            generate_all(config_path=config_file)

    def test_no_events_raises_runtime_error(
        self, temp_dir: Path, valid_config_toml: str
    ) -> None:
        """RuntimeError raised when ICS files contain no VEVENT entries."""
        config_file = temp_dir / "config.toml"
        config_file.write_text(valid_config_toml)
        cache_dir = temp_dir / "cache"
        cache_dir.mkdir()
        data_dir = temp_dir / "data"
        data_dir.mkdir()

        # Valid ICS with no events
        empty_ics = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = empty_ics

        with (
            patch("central_f10.data_importer.CACHE_DIR", cache_dir),
            patch(
                "central_f10.data_importer.GAMES_JSON",
                data_dir / "games.json",
            ),
            patch(
                "central_f10.data_importer.GAMES_TSV",
                data_dir / "games.tsv",
            ),
            patch(
                "central_f10.data_importer.CALENDAR_ICS",
                data_dir / "calendar.ics",
            ),
            patch(
                "central_f10.data_importer.requests.get",
                return_value=mock_response,
            ),
            patch("central_f10.data_importer.ensure_dirs"),
            pytest.raises(RuntimeError, match="No events found"),
        ):
            generate_all(config_path=config_file)
