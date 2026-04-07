"""Mock spectrum-analyzer implementation."""

from __future__ import annotations

from datetime import datetime

import numpy as np

from nfs_scanner.core.models import SpectrumAcquisitionResult, SpectrumConfig

from .base_spectrum import SpectrumAnalyzer
from .exceptions import SpectrumConfigurationError, SpectrumQueryError
from .utils import build_frequency_axis, normalize_frequency_window, parse_frequency_value, parse_numeric_value


class MockSpectrumAnalyzer(SpectrumAnalyzer):
    """Generate synthetic traces for spectrum workflow testing."""

    TRACE_POINTS = 1001
    instrument_type = "Mock-Spectrum"

    def __init__(self) -> None:
        self._connected = False
        self._config = SpectrumConfig()
        self._rng = np.random.default_rng(20260313)
        self._continuous_enabled = True
        self.resource_name = "mock://local"

    def connect(self) -> bool:
        """Simulate opening a spectrum-analyzer connection."""

        self._connected = True
        return True

    def disconnect(self) -> None:
        """Simulate closing a spectrum-analyzer connection."""

        self._connected = False

    def get_idn(self) -> str:
        """Return one deterministic mock ID string."""

        self._ensure_connected()
        return "NFS,Mock-Spectrum,2026,1.0"

    def preset(self) -> None:
        """Reset the mock analyzer configuration to defaults."""

        self._ensure_connected()
        self._config = SpectrumConfig()

    def set_center_freq(self, frequency_hz: float) -> None:
        """Apply one center frequency in Hz."""

        self.set_setting("center_freq", frequency_hz)

    def set_span(self, span_hz: float) -> None:
        """Apply one span in Hz."""

        self.set_setting("span", span_hz)

    def set_start_stop_freq(self, start_hz: float, stop_hz: float) -> None:
        """Apply one start/stop sweep window in Hz."""

        self.set_setting("start_freq", start_hz)
        self.set_setting("stop_freq", stop_hz)

    def set_rbw(self, rbw_hz: float) -> None:
        """Apply one RBW in Hz."""

        self.set_setting("rbw", rbw_hz)

    def set_vbw(self, vbw_hz: float) -> None:
        """Apply one VBW in Hz."""

        self.set_setting("vbw", vbw_hz)

    def set_ref_level(self, ref_level_dbm: float) -> None:
        """Apply one reference level in dBm."""

        self.set_setting("ref_level", ref_level_dbm)

    def set_detector(self, detector: str) -> None:
        """Apply one detector mode."""

        self.set_setting("detector", detector)

    def set_trace_mode(self, trace_mode: str) -> None:
        """Apply one trace mode."""

        self.set_setting("trace_mode", trace_mode)

    def set_continuous(self, enabled: bool) -> None:
        """Toggle the mock continuous mode flag."""

        self._ensure_connected()
        self._continuous_enabled = enabled

    def query_setting(self, setting_key: str) -> str:
        """Return one normalized mock setting as raw text."""

        self._ensure_connected()
        frequency_settings = self._current_frequency_settings()
        if setting_key == "start_freq":
            return self._format_optional_float(frequency_settings.start_freq_hz)
        if setting_key == "stop_freq":
            return self._format_optional_float(frequency_settings.stop_freq_hz)
        if setting_key == "center_freq":
            return self._format_optional_float(frequency_settings.center_freq_hz)
        if setting_key == "span":
            return self._format_optional_float(frequency_settings.span_hz)
        if setting_key == "rbw":
            return self._format_optional_float(parse_frequency_value(self._config.rbw))
        if setting_key == "vbw":
            return self._format_optional_float(parse_frequency_value(self._config.vbw))
        if setting_key == "ref_level":
            return self._format_optional_float(parse_numeric_value(self._config.ref_level))
        if setting_key == "points":
            return str(self.TRACE_POINTS)
        if setting_key == "scale":
            return "10"
        if setting_key == "detector":
            return self._config.detector or "RMS"
        if setting_key == "trace_mode":
            return self._config.trace_mode or "WRIT"
        raise SpectrumQueryError(f"Unsupported mock setting query: {setting_key}")

    def set_setting(self, setting_key: str, value: str | float | int) -> None:
        """Apply one normalized mock setting."""

        self._ensure_connected()
        if setting_key not in {
            "start_freq",
            "stop_freq",
            "center_freq",
            "span",
            "rbw",
            "vbw",
            "ref_level",
            "detector",
            "trace_mode",
        }:
            raise SpectrumConfigurationError(f"Unsupported mock setting update: {setting_key}")

        text_value = str(value).strip()
        if setting_key == "detector":
            self._config.detector = text_value
            return
        if setting_key == "trace_mode":
            self._config.trace_mode = text_value
            return
        setattr(self._config, setting_key, text_value)

    def configure(self, config: SpectrumConfig) -> None:
        """Store one placeholder spectrum configuration."""

        self._ensure_connected()
        self._config = config

    def trigger_single(self) -> None:
        """Accept the single-trigger request without extra delay."""

        self._ensure_connected()

    def wait_opc(self, timeout_ms: int | None = None) -> None:
        """The mock instrument always completes immediately."""

        del timeout_ms
        self._ensure_connected()

    def fetch_trace(self) -> SpectrumAcquisitionResult:
        """Generate one synthetic trace payload."""

        self._ensure_connected()
        frequency_settings = self._current_frequency_settings()
        start_hz = frequency_settings.start_freq_hz or 1.0e6
        stop_hz = frequency_settings.stop_freq_hz or (start_hz + 1.0e6)
        if stop_hz <= start_hz:
            stop_hz = start_hz + 1.0e6

        frequencies = build_frequency_axis(start_hz, stop_hz, self.TRACE_POINTS)
        span = stop_hz - start_hz

        baseline = -82.0 + 2.0 * np.sin(np.linspace(0.0, 6.0 * np.pi, self.TRACE_POINTS))
        peak_one = 24.0 * np.exp(-((frequencies - (start_hz + span * 0.28)) ** 2) / (2.0 * (span * 0.035) ** 2))
        peak_two = 18.0 * np.exp(-((frequencies - (start_hz + span * 0.72)) ** 2) / (2.0 * (span * 0.055) ** 2))
        noise = self._rng.normal(0.0, 0.9, self.TRACE_POINTS)
        trace_values = (baseline + peak_one + peak_two + noise).astype(np.float64)

        return SpectrumAcquisitionResult(
            instrument_type=self.instrument_type,
            timestamp=datetime.now(),
            acquisition_mode="trace",
            frequency_settings=frequency_settings,
            rbw_hz=parse_frequency_value(self._config.rbw),
            vbw_hz=parse_frequency_value(self._config.vbw),
            ref_level_dbm=parse_numeric_value(self._config.ref_level),
            detector=self._config.detector or "RMS",
            trace_mode=self._config.trace_mode or "WRIT",
            trace_frequencies_hz=frequencies,
            trace_values=trace_values,
            point_value=float(np.max(trace_values)),
            metadata={
                "resource_name": self.resource_name,
                "continuous_enabled": self._continuous_enabled,
            },
        )

    def fetch_point_value(self) -> SpectrumAcquisitionResult:
        """Return one point-style result derived from the current trace."""

        trace_result = self.fetch_trace()
        return SpectrumAcquisitionResult(
            instrument_type=trace_result.instrument_type,
            timestamp=trace_result.timestamp,
            acquisition_mode="point",
            frequency_settings=trace_result.frequency_settings,
            rbw_hz=trace_result.rbw_hz,
            vbw_hz=trace_result.vbw_hz,
            ref_level_dbm=trace_result.ref_level_dbm,
            detector=trace_result.detector,
            trace_mode=trace_result.trace_mode,
            trace_frequencies_hz=trace_result.trace_frequencies_hz,
            trace_values=trace_result.trace_values,
            point_value=trace_result.point_value,
            metadata=trace_result.metadata,
        )

    def acquire_spectrum(self) -> SpectrumAcquisitionResult:
        """Acquire one mock measurement using the current acquisition mode."""

        self._ensure_connected()
        if self._config.acquisition_mode == "point":
            return self.fetch_point_value()
        return self.fetch_trace()

    def _ensure_connected(self) -> None:
        """Guard operations that require a connection."""

        if not self._connected:
            raise RuntimeError("Mock spectrum analyzer is not connected.")

    def _current_frequency_settings(self):
        """Return the normalized sweep window for the current mock config."""

        return normalize_frequency_window(
            start_freq_hz=parse_frequency_value(self._config.start_freq),
            stop_freq_hz=parse_frequency_value(self._config.stop_freq),
            center_freq_hz=parse_frequency_value(self._config.center_freq),
            span_hz=parse_frequency_value(self._config.span),
        )

    def _format_optional_float(self, value: float | None) -> str:
        """Format one optional float as a SCPI-like raw value string."""

        if value is None:
            return ""
        return f"{value:.6f}"
