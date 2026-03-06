"""Tests for data_importer module."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_importer import _is_valid_ics_content


class TestIsValidIcsContent:
    """Tests for _is_valid_ics_content function."""

    def test_is_valid_ics_content_valid(self, sample_ics_content: bytes) -> None:
        """Valid ICS content returns True."""
        assert _is_valid_ics_content(sample_ics_content) is True

    def test_is_valid_ics_content_html(self, sample_html_content: bytes) -> None:
        """HTML content returns False."""
        assert _is_valid_ics_content(sample_html_content) is False

    def test_is_valid_ics_content_empty(self) -> None:
        """Empty content returns False."""
        assert _is_valid_ics_content(b"") is False

    def test_is_valid_ics_content_garbage(self) -> None:
        """Garbage content returns False."""
        assert _is_valid_ics_content(b"\x00\x01\x02\x03") is False

    def test_is_valid_ics_content_case_insensitive(self) -> None:
        """ICS detection is case insensitive."""
        # The function lowercases before checking
        content = b"BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR"
        assert _is_valid_ics_content(content) is True
