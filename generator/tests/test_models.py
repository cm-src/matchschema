"""Tests for Pydantic models."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import GameEvent


class TestGameEvent:
    """Tests for GameEvent model validation."""

    def test_game_event_valid(self) -> None:
        """Valid event passes validation."""
        event = GameEvent(
            team="Central F10 Vinröd",
            game="Central F10 Vinröd vs Opponent",
            starttm=datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),
            endtm=datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
            location="Sports Hall Arena",
            gameid="test123",
            url="https://profixio.com/game/123",
            team_slug="vinrod",
            team_display="Vinröd",
            team_color="#550f38",
        )
        assert event.team == "Central F10 Vinröd"
        assert event.game == "Central F10 Vinröd vs Opponent"
        assert event.location == "Sports Hall Arena"
        assert event.team_slug == "vinrod"
        assert event.team_display == "Vinröd"
        assert event.team_color == "#550f38"

    def test_game_event_missing_required(self) -> None:
        """Missing required field raises ValidationError."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            GameEvent(
                team="Central F10",
                game="Game",
                # Missing starttm, endtm, location, gameid, url, team_slug, team_display, team_color
            )

    def test_game_event_end_before_start(self) -> None:
        """End time before start time raises ValidationError."""
        with pytest.raises(Exception, match="must be after"):
            GameEvent(
                team="Central F10",
                game="Game",
                starttm=datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
                endtm=datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),  # Before start
                location="Arena",
                gameid="test",
                url="https://example.com",
                team_slug="team",
                team_display="Team",
                team_color="#550f38",
            )

    def test_game_event_strips_whitespace(self) -> None:
        """String fields have whitespace stripped."""
        event = GameEvent(
            team="  Central F10  ",
            game="  Game  ",
            starttm=datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),
            endtm=datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
            location="  Arena  ",
            gameid="  test  ",
            url="  https://example.com  ",
            team_slug="  team  ",
            team_display="  Team  ",
            team_color="  #550f38  ",
        )
        assert event.team == "Central F10"
        assert event.game == "Game"
        assert event.location == "Arena"
        assert event.gameid == "test"
        assert event.url == "https://example.com"
        assert event.team_slug == "team"
        assert event.team_display == "Team"
        assert event.team_color == "#550f38"

    def test_game_event_model_validate(self) -> None:
        """model_validate works with dict input."""
        data = {
            "team": "Central F10",
            "game": "Game",
            "starttm": datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),
            "endtm": datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
            "location": "Arena",
            "gameid": "test",
            "url": "https://example.com",
            "team_slug": "team",
            "team_display": "Team",
            "team_color": "#550f38",
        }
        event = GameEvent.model_validate(data)
        assert event.team == "Central F10"
        assert event.team_slug == "team"

    def test_game_event_invalid_color(self) -> None:
        """Invalid hex color raises ValidationError."""
        with pytest.raises(Exception, match="hex color"):
            GameEvent(
                team="Central F10",
                game="Game",
                starttm=datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),
                endtm=datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
                location="Arena",
                gameid="test",
                url="https://example.com",
                team_slug="team",
                team_display="Team",
                team_color="red",  # Invalid - not a 7-char hex
            )

    def test_game_event_valid_url_http(self) -> None:
        """HTTP URL is accepted."""
        event = GameEvent(
            team="Central F10",
            game="Game",
            starttm=datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),
            endtm=datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
            location="Arena",
            gameid="test",
            url="http://example.com/game",
            team_slug="team",
            team_display="Team",
            team_color="#550f38",
        )
        assert event.url == "http://example.com/game"

    def test_game_event_valid_url_https(self) -> None:
        """HTTPS URL is accepted."""
        event = GameEvent(
            team="Central F10",
            game="Game",
            starttm=datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),
            endtm=datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
            location="Arena",
            gameid="test",
            url="https://profixio.com/game/123",
            team_slug="team",
            team_display="Team",
            team_color="#550f38",
        )
        assert event.url == "https://profixio.com/game/123"

    def test_game_event_invalid_url_protocol(self) -> None:
        """Non-HTTP(S) URL raises ValidationError."""
        with pytest.raises(Exception, match="http or https protocol"):
            GameEvent(
                team="Central F10",
                game="Game",
                starttm=datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),
                endtm=datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
                location="Arena",
                gameid="test",
                url="ftp://example.com",
                team_slug="team",
                team_display="Team",
                team_color="#550f38",
            )

    def test_game_event_invalid_url_no_host(self) -> None:
        """URL without host raises ValidationError."""
        with pytest.raises(Exception, match="valid host"):
            GameEvent(
                team="Central F10",
                game="Game",
                starttm=datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc),
                endtm=datetime(2025, 3, 15, 16, 0, tzinfo=timezone.utc),
                location="Arena",
                gameid="test",
                url="https://",
                team_slug="team",
                team_display="Team",
                team_color="#550f38",
            )
