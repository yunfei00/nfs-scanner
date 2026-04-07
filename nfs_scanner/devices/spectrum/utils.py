"""Helpers shared by spectrum-analyzer adapters."""

from __future__ import annotations

import re

import numpy as np
from numpy.typing import NDArray

from nfs_scanner.core.models import SpectrumFrequencySettings

_FREQUENCY_PATTERN = re.compile(
    r"^\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*([kmg]?)(?:hz)?\s*$",
    re.IGNORECASE,
)
_NUMERIC_PATTERN = re.compile(
    r"^\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)(?:\s*[a-zA-Z%/]+)?\s*$",
    re.IGNORECASE,
)
_UNIT_FACTORS = {
    "": 1.0,
    "k": 1.0e3,
    "m": 1.0e6,
    "g": 1.0e9,
}


def parse_frequency_value(value: str | float | int | None) -> float | None:
    """Parse one engineering frequency string into Hz."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    normalized = value.strip()
    if not normalized:
        return None

    match = _FREQUENCY_PATTERN.match(normalized)
    if match is None:
        raise ValueError(f"Unsupported frequency value: {value!r}")

    magnitude = float(match.group(1))
    unit = match.group(2).lower()
    return magnitude * _UNIT_FACTORS[unit]


def parse_numeric_value(value: str | float | int | None) -> float | None:
    """Parse one numeric SCPI value with an optional textual suffix."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    normalized = value.strip()
    if not normalized:
        return None

    match = _NUMERIC_PATTERN.match(normalized)
    if match is None:
        raise ValueError(f"Unsupported numeric value: {value!r}")
    return float(match.group(1))


def parse_ascii_float_values(raw_text: str) -> NDArray[np.float64]:
    """Parse one comma or whitespace separated float payload."""

    tokens = [
        token
        for token in re.split(r"[\s,]+", raw_text.strip())
        if token
    ]
    if not tokens:
        raise ValueError("Trace payload is empty.")
    return np.asarray([float(token) for token in tokens], dtype=np.float64)


def build_frequency_axis(
    start_freq_hz: float | None,
    stop_freq_hz: float | None,
    point_count: int,
) -> NDArray[np.float64]:
    """Build a linear frequency axis from the reported sweep window."""

    if point_count <= 0:
        raise ValueError("Point count must be greater than zero.")
    if start_freq_hz is None or stop_freq_hz is None:
        return np.arange(point_count, dtype=np.float64)
    if point_count == 1:
        return np.asarray([start_freq_hz], dtype=np.float64)
    return np.linspace(start_freq_hz, stop_freq_hz, point_count, dtype=np.float64)


def normalize_frequency_window(
    *,
    start_freq_hz: float | None,
    stop_freq_hz: float | None,
    center_freq_hz: float | None,
    span_hz: float | None,
) -> SpectrumFrequencySettings:
    """Normalize the frequency window and derive missing companion values."""

    start_value = start_freq_hz
    stop_value = stop_freq_hz
    center_value = center_freq_hz
    span_value = span_hz

    if start_value is None and center_value is not None and span_value is not None:
        start_value = center_value - span_value / 2.0
    if stop_value is None and center_value is not None and span_value is not None:
        stop_value = center_value + span_value / 2.0
    if center_value is None and start_value is not None and stop_value is not None:
        center_value = (start_value + stop_value) / 2.0
    if span_value is None and start_value is not None and stop_value is not None:
        span_value = stop_value - start_value

    return SpectrumFrequencySettings(
        start_freq_hz=start_value,
        stop_freq_hz=stop_value,
        center_freq_hz=center_value,
        span_hz=span_value,
    )
