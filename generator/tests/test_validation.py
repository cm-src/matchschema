"""Tests for shared validation helpers."""

import pytest

from central_f10.validation import validate_hex_color, validate_http_url


class TestValidateHexColor:
    def test_valid_hex(self) -> None:
        assert validate_hex_color("#550f38") == "#550f38"
        assert validate_hex_color("#FEC225") == "#FEC225"

    @pytest.mark.parametrize("value", ["red", "#fff", "#550f38 ", "550f38", ""])
    def test_invalid_hex_raises(self, value: str) -> None:
        with pytest.raises(ValueError, match="hex color"):
            validate_hex_color(value)


class TestValidateHttpUrl:
    def test_valid_http_https(self) -> None:
        assert validate_http_url("https://example.com/x") == "https://example.com/x"
        assert validate_http_url("http://example.com/y") == "http://example.com/y"

    @pytest.mark.parametrize("value", ["ftp://x", "https://", "not-a-url"])
    def test_invalid_raises(self, value: str) -> None:
        with pytest.raises(ValueError):
            validate_http_url(value)

    def test_empty_rejected_by_default(self) -> None:
        """IcsFileEntry semantics: empty URL is invalid (required field)."""
        with pytest.raises(ValueError):
            validate_http_url("")

    def test_empty_allowed_when_opted_in(self) -> None:
        """GameEvent semantics: empty URL is accepted."""
        assert validate_http_url("", allow_empty=True) == ""
