"""Shared version parsing and compatibility helpers."""

from __future__ import annotations

from typing import Any


def parse_version(version_str: str | None) -> tuple[int, ...]:
    """Parse a dotted version string into an integer tuple.

    Non-numeric suffixes are ignored to keep parsing tolerant.
    Invalid or empty values return ``(0,)``.
    """

    if not isinstance(version_str, str):
        return (0,)

    normalized = version_str.strip()
    if not normalized:
        return (0,)

    parts: list[int] = []
    for token in normalized.split("."):
        digits = "".join(character for character in token if character.isdigit())
        if not digits:
            break
        parts.append(int(digits))

    return tuple(parts) if parts else (0,)


def get_major(version_str: str | None) -> int:
    """Return the major version number for a dotted version string."""

    return parse_version(version_str)[0]


def is_major_compatible(current: str | None, target: str | None) -> bool:
    """Return whether two versions are compatible by major version only."""

    return get_major(current) == get_major(target)


def safe_version_str(value: Any, default: str) -> str:
    """Normalize one version-like value to a non-empty string."""

    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


__all__ = [
    "get_major",
    "is_major_compatible",
    "parse_version",
    "safe_version_str",
]
