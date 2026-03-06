"""Integration tests for the full pipeline."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestIntegration:
    """End-to-end pipeline tests."""

    def test_read_ical_parses_events(
        self, temp_dir: Path, sample_ics_content: bytes, minimal_team_meta: dict
    ) -> None:
        """read_ical correctly parses ICS content."""
        from data_importer import read_ical

        ics_file = temp_dir / "test.ics"
        ics_file.write_bytes(sample_ics_content)

        events = read_ical(
            ics_file,
            team_name=minimal_team_meta["team_name"],
            team_slug=minimal_team_meta["team_slug"],
            team_display=minimal_team_meta["team_display"],
            team_color=minimal_team_meta["team_color"],
        )

        assert len(events) == 1
        event = events[0]
        assert event.team == "Central F10 Vinröd"
        assert "Central F10 Vinrod vs Opponent" in event.game
        assert event.location == "Sports Hall Arena"
        assert event.gameid == "test123"
        assert event.team_slug == "vinrod"
        assert event.team_display == "Vinröd"
        assert event.team_color == "#550f38"

    def test_read_ical_handles_team_name_from_config(
        self, temp_dir: Path, sample_ics_content: bytes
    ) -> None:
        """read_ical uses team_name from config, not ICS."""
        from data_importer import read_ical

        ics_file = temp_dir / "test.ics"
        ics_file.write_bytes(sample_ics_content)

        events = read_ical(
            ics_file,
            team_name="Custom Team Name",
            team_slug="custom",
            team_display="Custom",
            team_color="#000000",
        )

        assert len(events) == 1
        assert events[0].team == "Custom Team Name"
        assert events[0].team_slug == "custom"

    def test_generate_json_structure(self, temp_dir: Path) -> None:
        """Generated JSON has correct structure."""
        import json

        from data_importer import GameEvent, generate_json

        events = [
            GameEvent(
                team="Central F10 Vinröd",
                game="Central F10 Vinröd vs Opponent",
                starttm=datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),
                endtm=datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
                location="Arena",
                gameid="test123",
                url="https://profixio.com/game/123",
                team_slug="vinrod",
                team_display="Vinröd",
                team_color="#550f38",
            )
        ]

        output_file = temp_dir / "games.json"

        with patch("data_importer.GAMES_JSON", output_file):
            generate_json(events)

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert "updated" in data
        assert "games" in data
        assert len(data["games"]) == 1
        assert data["games"][0]["team"] == "vinrod"
        assert data["games"][0]["teamDisplay"] == "Vinröd"
        assert data["games"][0]["teamColor"] == "#550f38"

    def test_generate_tsv_structure(self, temp_dir: Path) -> None:
        """Generated TSV has correct structure."""
        from data_importer import GameEvent, generate_tsv

        events = [
            GameEvent(
                team="Central F10",
                game="Game 1",
                starttm=datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),
                endtm=datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
                location="Arena",
                gameid="test",
                url="https://example.com",
                team_slug="team",
                team_display="Team",
                team_color="#550f38",
            )
        ]

        output_file = temp_dir / "games.tsv"

        with patch("data_importer.GAMES_TSV", output_file):
            generate_tsv(events)

        assert output_file.exists()
        lines = output_file.read_text().strip().split("\n")
        assert lines[0] == "team\tgame\tlocation\tstart\tend\turl"
        assert len(lines) == 2  # header + 1 data row

    def test_generate_ics_structure(self, temp_dir: Path) -> None:
        """Generated ICS has correct structure."""
        from data_importer import GameEvent, generate_ics

        events = [
            GameEvent(
                team="Central F10",
                game="Game 1",
                starttm=datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),
                endtm=datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
                location="Arena",
                gameid="test",
                url="https://example.com",
                team_slug="team",
                team_display="Team",
                team_color="#550f38",
            )
        ]

        output_file = temp_dir / "calendar.ics"

        with patch("data_importer.CALENDAR_ICS", output_file):
            generate_ics(events)

        assert output_file.exists()
        content = output_file.read_text()
        assert "BEGIN:VCALENDAR" in content
        assert "BEGIN:VEVENT" in content
        assert "Central F10" in content
