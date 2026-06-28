"""Tests for the app.py CLI entry point."""

from pathlib import Path
from unittest.mock import patch

import app


class TestMain:
    """Tests for app.main exit codes."""

    def test_success_returns_zero(self) -> None:
        """A successful generation returns exit code 0."""
        with patch("app.generate_all", return_value=5) as mock_gen:
            code = app.main(["--dry-run"])
        assert code == 0
        mock_gen.assert_called_once()
        assert mock_gen.call_args.kwargs.get("dry_run") is True

    def test_file_not_found_returns_one(self) -> None:
        """FileNotFoundError maps to exit code 1."""
        with patch(
            "app.generate_all",
            side_effect=FileNotFoundError("missing config"),
        ):
            code = app.main([])
        assert code == 1

    def test_generic_error_returns_one(self) -> None:
        """Any other exception maps to exit code 1."""
        with patch(
            "app.generate_all",
            side_effect=RuntimeError("boom"),
        ):
            code = app.main([])
        assert code == 1


class TestParseArgs:
    """Tests for argument parsing."""

    def test_defaults(self) -> None:
        args = app.parse_args([])
        assert args.verbose is False
        assert args.quiet is False
        assert args.dry_run is False
        assert args.config is None

    def test_dry_run_flag(self) -> None:
        args = app.parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_config_path(self, tmp_path: Path) -> None:
        config = tmp_path / "custom.toml"
        args = app.parse_args(["--config", str(config)])
        assert args.config == config
