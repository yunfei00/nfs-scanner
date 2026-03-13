"""Mock spectrum-analyzer implementation."""

from __future__ import annotations

import re

import numpy as np
from numpy.typing import NDArray

from nfs_scanner.core.models import SpectrumConfig

from .base_spectrum import SpectrumAnalyzer

_FREQUENCY_PATTERN = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*([kmg]?)(?:hz)?\s*$", re.IGNORECASE)
_UNIT_FACTORS = {
    "": 1.0,
    "k": 1.0e3,
    "m": 1.0e6,
    "g": 1.0e9,
}


class MockSpectrumAnalyzer(SpectrumAnalyzer):
    """Generate synthetic traces for spectrum workflow testing."""

    TRACE_POINTS = 1001

    def __init__(self) -> None:
        self._connected = False
        self._config = SpectrumConfig()
        self._rng = np.random.default_rng(20260313)

    def connect(self) -> bool:
        """Simulate opening a spectrum-analyzer connection."""

        self._connected = True
        return True

    def disconnect(self) -> None:
        """Simulate closing a spectrum-analyzer connection."""

        self._connected = False

    def configure(self, config: SpectrumConfig) -> None:
        """Store one placeholder spectrum configuration."""

        self._ensure_connected()
        self._config = config

    def acquire_trace(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Generate one synthetic spectrum trace."""

        self._ensure_connected()

        start_hz = self._parse_frequency_value(self._config.start_freq)
        stop_hz = self._parse_frequency_value(self._config.stop_freq)
        if stop_hz <= start_hz:
            stop_hz = start_hz + 1.0e6

        frequencies = np.linspace(start_hz, stop_hz, self.TRACE_POINTS, dtype=np.float64)
        span = stop_hz - start_hz

        baseline = -82.0 + 2.0 * np.sin(np.linspace(0.0, 6.0 * np.pi, self.TRACE_POINTS))
        peak_one = 24.0 * np.exp(-((frequencies - (start_hz + span * 0.28)) ** 2) / (2.0 * (span * 0.035) ** 2))
        peak_two = 18.0 * np.exp(-((frequencies - (start_hz + span * 0.72)) ** 2) / (2.0 * (span * 0.055) ** 2))
        noise = self._rng.normal(0.0, 0.9, self.TRACE_POINTS)
        amplitudes = baseline + peak_one + peak_two + noise

        return frequencies, amplitudes.astype(np.float64)

    def _ensure_connected(self) -> None:
        """Guard operations that require a connection."""

        if not self._connected:
            raise RuntimeError("Mock spectrum analyzer is not connected.")

    def _parse_frequency_value(self, text: str) -> float:
        """Parse a frequency string like 100MHz or 3GHz into Hz."""

        match = _FREQUENCY_PATTERN.match(text)
        if match is None:
            raise ValueError(f"Unsupported frequency value: {text!r}")

        magnitude = float(match.group(1))
        unit = match.group(2).lower()
        return magnitude * _UNIT_FACTORS[unit]
