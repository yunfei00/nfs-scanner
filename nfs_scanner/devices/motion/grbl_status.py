"""GRBL/GRBL-like status line parsing (extracted from legacy ScanWorker)."""

from __future__ import annotations


def extract_latest_status_line(text: str, *, buffer: str = "") -> tuple[str | None, str]:
    """Return the latest ``<Idle|MPos:...>`` line and remaining buffer tail."""

    if not text and not buffer:
        return None, buffer

    combined = (buffer + text).replace("\r", "\n")
    lines = combined.split("\n")
    tail = lines.pop() if lines else ""

    latest: str | None = None
    for line in lines:
        cleaned = line.strip()
        if cleaned.startswith("<") and "|" in cleaned:
            latest = cleaned
    return latest, tail


def parse_motion_status(status_line: str) -> tuple[str, tuple[float, float, float] | None]:
    """Parse one GRBL status line into controller state and machine position."""

    if not status_line.startswith("<"):
        return "", None
    payload = status_line.strip("<>")
    head = payload.split("|", 1)[0]
    if "MPos:" not in payload:
        return head, None
    mpos_segment = payload.split("MPos:", 1)[1].split("|", 1)[0]
    values = mpos_segment.split(",")
    if len(values) < 3:
        return head, None
    try:
        return head, (float(values[0]), float(values[1]), float(values[2]))
    except ValueError:
        return head, None


def position_within_tolerance(
    current: tuple[float, float, float],
    target: tuple[float, float, float],
    tolerance: float,
) -> bool:
    return all(abs(cur - tar) <= tolerance for cur, tar in zip(current, target))
