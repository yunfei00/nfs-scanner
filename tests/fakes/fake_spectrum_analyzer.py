"""Fake spectrum instrument for integration tests."""

from __future__ import annotations

from datetime import datetime

import numpy as np

from nfs_scanner.core.models import SpectrumAcquisitionResult, SpectrumFrequencySettings
from nfs_scanner.devices.instruments.instrument_controller import InstrumentController
from nfs_scanner.devices.spectrum.mock_spectrum import MockSpectrumAnalyzer


class FakeSpectrumAnalyzer(MockSpectrumAnalyzer):
    def __init__(self, *, points: int = 11) -> None:
        super().__init__()
        self._points = points
        self.sweep_calls = 0

    def trigger_single(self) -> None:
        self.sweep_calls += 1
        super().trigger_single()

    def fetch_trace(self) -> SpectrumAcquisitionResult:
        frequencies = np.linspace(2.4e9, 2.5e9, self._points)
        amplitudes = np.linspace(-80.0, -20.0, self._points)
        return SpectrumAcquisitionResult(
            instrument_type="FakeSpectrum",
            timestamp=datetime.now(),
            acquisition_mode="trace",
            frequency_settings=SpectrumFrequencySettings(start_freq_hz=2.4e9, stop_freq_hz=2.5e9),
            trace_frequencies_hz=frequencies,
            trace_values=amplitudes,
            metadata={"mock": True},
        )


class FakeInstrumentController(InstrumentController):
    def __init__(self, *, points: int = 11) -> None:
        super().__init__(FakeSpectrumAnalyzer(points=points))
        self._connected = False
        self.abort_calls = 0

    def connect(self) -> bool:
        self._connected = bool(self.analyzer.connect())
        return self._connected

    def disconnect(self) -> None:
        self.analyzer.disconnect()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def identify(self) -> str:
        return "FakeSpectrum/1.0"

    def abort(self) -> None:
        self.abort_calls += 1
        super().abort()
