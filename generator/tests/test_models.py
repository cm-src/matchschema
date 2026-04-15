"""Tests for Pydantic models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from central_f10.models import GameEvent


def _base_event_kwargs(**overrides: object) -> dict:
    """Return valid GameEvent kwargs with optional overrides."""
    defaults = {
        "team": "Central F10 Vinröd",
        "game": "Central F10 Vinröd vs Opponent",
        "starttm": datetime(2025, 3, 15, 14, 0, tzinfo=UTC),
        "endtm": datetime(2025, 3, 15, 16, 0, tzinfo=UTC),
        "location": "Sports Hall Arena",
        "gameid": "test123",
        "url": "https://profixio.com/game/123",
        "team_slug": "vinrod",
        "team_display": "Vinröd",
        "team_color": "#550f38",
    }
    defaults.update(overrides)
    return defaults


class TestGameEvent:
    """Tests for GameEvent model validation."""

    def test_game_event_valid(self) -> None:
        """Valid event passes validation."""
        event = GameEvent(**_base_event_kwargs())
        assert event.team == "Central F10 Vinröd"
        assert event.game == "Central F10 Vinröd vs Opponent"
        assert event.location == "Sports Hall Arena"
        assert event.team_slug == "vinrod"
        assert event.team_display == "Vinröd"
        assert event.team_color == "#550f38"

    def test_game_event_missing_required(self) -> None:
        """Missing required field raises ValidationError."""
        with pytest.raises(ValidationError):
            GameEvent(
                team="Central F10",
                game="Game",
                # Missing starttm, endtm, location, gameid,
                # url, team_slug, team_display, team_color
            )

    def test_game_event_end_before_start(self) -> None:
        """End time before start time raises ValidationError."""
        with pytest.raises(ValidationError, match="must be after"):
            GameEvent(
                **_base_event_kwargs(
                    starttm=datetime(2025, 3, 15, 16, 0, tzinfo=UTC),
                    endtm=datetime(2025, 3, 15, 14, 0, tzinfo=UTC),
                )
            )

    @pytest.mark.parametrize(
        "field,raw,expected",
        [
            ("team", "  Central F10  ", "Central F10"),
            ("game", "  Game  ", "Game"),
            ("location", "  Arena  ", "Arena"),
            ("gameid", "  test  ", "test"),
            ("url", "  https://example.com  ", "https://example.com"),
            ("team_slug", "  team  ", "team"),
            ("team_display", "  Team  ", "Team"),
            ("team_color", "  #550f38  ", "#550f38"),
        ],
    )
    def test_game_event_strips_whitespace(
        self, field: str, raw: str, expected: str
    ) -> None:
        """String fields have whitespace stripped."""
        event = GameEvent(**_base_event_kwargs(**{field: raw}))
        assert getattr(event, field) == expected

    def test_game_event_model_validate(self) -> None:
        """model_validate works with dict input."""
        event = GameEvent.model_validate(_base_event_kwargs())
        assert event.team == "Central F10 Vinröd"
        assert event.team_slug == "vinrod"

    @pytest.mark.parametrize(
        "color",
        ["red", "#123", "#GGGGGG", "550f38", "#550f3"],
    )
    def test_game_event_invalid_color(self, color: str) -> None:
        """Invalid hex color raises ValidationError."""
        with pytest.raises(ValidationError, match="hex color"):
            GameEvent(**_base_event_kwargs(team_color=color))

    @pytest.mark.parametrize(
        "url", ["http://example.com/game", "https://profixio.com/game/123"]
    )
    def test_game_event_valid_url(self, url: str) -> None:
        """HTTP(S) URLs are accepted."""
        event = GameEvent(**_base_event_kwargs(url=url))
        assert event.url == url

    @pytest.mark.parametrize(
        "url,match",
        [
            ("ftp://example.com", "http or https protocol"),
            ("https://", "valid host"),
        ],
    )
    def test_game_event_invalid_url(self, url: str, match: str) -> None:
        """Invalid URLs raise ValidationError."""
        with pytest.raises(ValidationError, match=match):
            GameEvent(**_base_event_kwargs(url=url))

    def test_game_event_extra_fields_forbidden(self) -> None:
        """Unknown fields are rejected by the model."""
        with pytest.raises(ValidationError, match="extra"):
            GameEvent(
                **_base_event_kwargs(unknown_field="should be rejected"),
            )
