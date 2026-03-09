"""Tests for ICS config loading and validation."""

import importlib
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestLoadIcsFiles:
    """Tests for load_ics_files function."""

    def test_load_ics_files_valid(self, temp_dir: Path, valid_config_toml: str) -> None:
        """Valid config loads correctly."""
        config_file = temp_dir / "config.toml"
        config_file.write_text(valid_config_toml)

        # Patch paths.CONFIG_FILE and reload ics_config to pick up the change
        import paths

        original = paths.CONFIG_FILE
        paths.CONFIG_FILE = config_file

        # Reload ics_config to use the patched paths
        import ics_config

        importlib.reload(ics_config)

        try:
            result = ics_config.load_ics_files()
            assert len(result) == 2
            assert result[0]["url"] == "https://profixio.com/calendar1.ics"
            assert result[0]["filename"] == "team1.ics"
            assert result[0]["team_name"] == "Central F10 Vinröd"
            assert result[0]["team_slug"] == "vinrod"
            assert result[0]["team_display"] == "Vinröd"
            assert result[0]["team_color"] == "#550f38"
        finally:
            paths.CONFIG_FILE = original
            importlib.reload(ics_config)

    def test_load_ics_files_missing_file(self, temp_dir: Path) -> None:
        """Missing config file raises FileNotFoundError."""
        import paths

        paths.CONFIG_FILE = temp_dir / "nonexistent.toml"

        import ics_config

        importlib.reload(ics_config)

        with pytest.raises(FileNotFoundError, match="Config file not found"):
            ics_config.load_ics_files()

    def test_load_ics_files_missing_url(self, temp_dir: Path) -> None:
        """Missing url field raises ValueError."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[ics]
[[ics.files]]
filename = "team1.ics"
team_name = "Team"
team_slug = "team"
team_display = "Team"
team_color = "#550f38"
""")

        import paths

        paths.CONFIG_FILE = config_file

        import ics_config

        importlib.reload(ics_config)

        with pytest.raises(ValueError, match="missing required field 'url'"):
            ics_config.load_ics_files()

    def test_load_ics_files_missing_filename(self, temp_dir: Path) -> None:
        """Missing filename field raises ValueError."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[ics]
[[ics.files]]
url = "https://profixio.com/calendar.ics"
team_name = "Team"
team_slug = "team"
team_display = "Team"
team_color = "#550f38"
""")

        import paths

        paths.CONFIG_FILE = config_file

        import ics_config

        importlib.reload(ics_config)

        with pytest.raises(ValueError, match="missing required field 'filename'"):
            ics_config.load_ics_files()

    def test_load_ics_files_missing_team_slug(self, temp_dir: Path) -> None:
        """Missing team_slug field raises ValueError."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[ics]
[[ics.files]]
url = "https://profixio.com/calendar.ics"
filename = "team1.ics"
team_name = "Team"
team_display = "Team"
team_color = "#550f38"
""")

        import paths

        paths.CONFIG_FILE = config_file

        import ics_config

        importlib.reload(ics_config)

        with pytest.raises(ValueError, match="missing required field 'team_slug'"):
            ics_config.load_ics_files()

    def test_load_ics_files_missing_team_display(self, temp_dir: Path) -> None:
        """Missing team_display field raises ValueError."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[ics]
[[ics.files]]
url = "https://profixio.com/calendar.ics"
filename = "team1.ics"
team_name = "Team"
team_slug = "team"
team_color = "#550f38"
""")

        import paths

        paths.CONFIG_FILE = config_file

        import ics_config

        importlib.reload(ics_config)

        with pytest.raises(ValueError, match="missing required field 'team_display'"):
            ics_config.load_ics_files()

    def test_load_ics_files_missing_team_color(self, temp_dir: Path) -> None:
        """Missing team_color field raises ValueError."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[ics]
[[ics.files]]
url = "https://profixio.com/calendar.ics"
filename = "team1.ics"
team_name = "Team"
team_slug = "team"
team_display = "Team"
""")

        import paths

        paths.CONFIG_FILE = config_file

        import ics_config

        importlib.reload(ics_config)

        with pytest.raises(ValueError, match="missing required field 'team_color'"):
            ics_config.load_ics_files()

    def test_load_ics_files_invalid_url(self, temp_dir: Path) -> None:
        """Non-http URL raises ValueError."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[ics]
[[ics.files]]
url = "ftp://invalid.com/calendar.ics"
filename = "team1.ics"
team_name = "Team"
team_slug = "team"
team_display = "Team"
team_color = "#550f38"
""")

        import paths

        paths.CONFIG_FILE = config_file

        import ics_config

        importlib.reload(ics_config)

        with pytest.raises(ValueError, match="URL must start with http"):
            ics_config.load_ics_files()

    def test_load_ics_files_invalid_extension(self, temp_dir: Path) -> None:
        """Non-.ics filename raises ValueError."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[ics]
[[ics.files]]
url = "https://profixio.com/calendar.ics"
filename = "team1.txt"
team_name = "Team"
team_slug = "team"
team_display = "Team"
team_color = "#550f38"
""")

        import paths

        paths.CONFIG_FILE = config_file

        import ics_config

        importlib.reload(ics_config)

        with pytest.raises(ValueError, match="filename must end with .ics"):
            ics_config.load_ics_files()

    def test_load_ics_files_invalid_color(self, temp_dir: Path) -> None:
        """Invalid hex color raises ValueError."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[ics]
[[ics.files]]
url = "https://profixio.com/calendar.ics"
filename = "team1.ics"
team_name = "Team"
team_slug = "team"
team_display = "Team"
team_color = "red"
""")

        import paths

        paths.CONFIG_FILE = config_file

        import ics_config

        importlib.reload(ics_config)

        with pytest.raises(ValueError, match="team_color must be a valid hex color"):
            ics_config.load_ics_files()

    def test_load_ics_files_missing_ics_section(self, temp_dir: Path) -> None:
        """Missing [ics] section raises ValueError."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[other]
key = "value"
""")

        import paths

        paths.CONFIG_FILE = config_file

        import ics_config

        importlib.reload(ics_config)

        with pytest.raises(ValueError, match="Config missing required key"):
            ics_config.load_ics_files()
