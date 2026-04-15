"""Tests for ICS config loading and validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from central_f10.config import IcsFileEntry, load_ics_files


def _base_entry_kwargs(**overrides: object) -> dict:
    """Return valid IcsFileEntry kwargs with optional overrides."""
    defaults = {
        "url": "https://profixio.com/calendar.ics",
        "filename": "team1.ics",
        "team_name": "Team",
        "team_slug": "team",
        "team_display": "Team",
        "team_color": "#550f38",
    }
    defaults.update(overrides)
    return defaults


class TestIcsFileEntry:
    """Tests for IcsFileEntry Pydantic model."""

    def test_valid_entry(self) -> None:
        """Valid entry passes validation."""
        entry = IcsFileEntry(**_base_entry_kwargs())
        assert entry.url == "https://profixio.com/calendar.ics"
        assert entry.filename == "team1.ics"
        assert entry.team_name == "Team"

    @pytest.mark.parametrize(
        "field,value,match",
        [
            ("url", "ftp://invalid.com/calendar.ics", "http or https protocol"),
            ("filename", "team1.txt", "filename must end with .ics"),
            ("team_color", "red", "hex color"),
        ],
    )
    def test_invalid_field(self, field: str, value: str, match: str) -> None:
        """Invalid field value raises ValidationError."""
        with pytest.raises(ValidationError, match=match):
            IcsFileEntry(**_base_entry_kwargs(**{field: value}))

    def test_missing_required_field(self) -> None:
        """Missing required field raises ValidationError."""
        with pytest.raises(ValidationError):
            IcsFileEntry(
                url="https://profixio.com/calendar.ics",
                filename="team1.ics",
                # Missing team_name and others
            )

    def test_optional_division(self) -> None:
        """Division field is optional and defaults to None."""
        entry = IcsFileEntry(**_base_entry_kwargs())
        assert entry.division is None

    def test_model_validate_from_dict(self) -> None:
        """model_validate works with dict input (from TOML)."""
        entry = IcsFileEntry.model_validate(_base_entry_kwargs())
        assert entry.url == "https://profixio.com/calendar.ics"


class TestLoadIcsFiles:
    """Tests for load_ics_files function."""

    def test_load_ics_files_valid(self, temp_dir: Path, valid_config_toml: str) -> None:
        """Valid config loads correctly."""
        config_file = temp_dir / "config.toml"
        config_file.write_text(valid_config_toml)

        result = load_ics_files(config_file)
        assert len(result) == 2
        assert result[0].url == "https://profixio.com/calendar1.ics"
        assert result[0].filename == "team1.ics"
        assert result[0].team_name == "Central F10 Vinröd"
        assert result[0].team_slug == "vinrod"
        assert result[0].team_display == "Vinröd"
        assert result[0].team_color == "#550f38"

    def test_load_ics_files_missing_file(self, temp_dir: Path) -> None:
        """Missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_ics_files(temp_dir / "nonexistent.toml")

    @pytest.mark.parametrize(
        "missing_field",
        ["url", "filename", "team_slug", "team_display", "team_color"],
    )
    def test_load_ics_files_missing_required_field(
        self, temp_dir: Path, missing_field: str
    ) -> None:
        """Missing required field raises ValueError."""
        config_file = temp_dir / "config.toml"
        # Build a config missing one field
        fields = {
            "url": "https://profixio.com/calendar.ics",
            "filename": "team1.ics",
            "team_name": "Team",
            "team_slug": "team",
            "team_display": "Team",
            "team_color": "#550f38",
        }
        del fields[missing_field]
        lines = ["[ics]", "[[ics.files]]"]
        for k, v in fields.items():
            lines.append(f'{k} = "{v}"')
        config_file.write_text("\n".join(lines))

        with pytest.raises(
            ValueError,
            match=missing_field,
        ):
            load_ics_files(config_file)

    @pytest.mark.parametrize(
        "field,value,match",
        [
            ("url", "ftp://invalid.com/calendar.ics", "http or https protocol"),
            ("filename", "team1.txt", "filename must end with .ics"),
            ("team_color", "red", "hex color"),
        ],
    )
    def test_load_ics_files_invalid_field(
        self, temp_dir: Path, field: str, value: str, match: str
    ) -> None:
        """Invalid field in config raises ValueError."""
        base = {
            "url": "https://profixio.com/calendar.ics",
            "filename": "team1.ics",
            "team_name": "Team",
            "team_slug": "team",
            "team_display": "Team",
            "team_color": "#550f38",
        }
        base[field] = value

        lines = ["[ics]", "[[ics.files]]"]
        for k, v in base.items():
            lines.append(f'{k} = "{v}"')

        config_file = temp_dir / "config.toml"
        config_file.write_text("\n".join(lines))

        with pytest.raises(ValueError, match=match):
            load_ics_files(config_file)

    def test_load_ics_files_missing_ics_section(self, temp_dir: Path) -> None:
        """Missing [ics] section raises ValueError."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[other]
key = "value"
""")

        with pytest.raises(ValueError, match="Config missing required key"):
            load_ics_files(config_file)
