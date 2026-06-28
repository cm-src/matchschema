"""Shared validation helpers for Pydantic models.

Kept module-level (not inherited) so each model controls the order its
field validators run — e.g. GameEvent strips whitespace before validating.
"""

import re
from urllib.parse import urlparse

# Hex color pattern: # followed by exactly 6 hex characters
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def validate_hex_color(v: str) -> str:
    """Validate a 6-digit hex color like '#550f38'."""
    if not HEX_COLOR_PATTERN.match(v):
        raise ValueError(
            f"team_color must be a valid hex color like '#550f38', got '{v}'"
        )
    return v


def validate_http_url(v: str, *, allow_empty: bool = False) -> str:
    """Validate an http/https URL with a host.

    Args:
        v: The URL string to validate.
        allow_empty: If True, an empty string is accepted (e.g. GameEvent's
            optional URL). If False, an empty string fails like any other
            invalid URL.
    """
    if allow_empty and not v:
        return v
    parsed = urlparse(v)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL must use http or https protocol, got '{v}'")
    if not parsed.netloc:
        raise ValueError(f"URL must have a valid host, got '{v}'")
    return v
