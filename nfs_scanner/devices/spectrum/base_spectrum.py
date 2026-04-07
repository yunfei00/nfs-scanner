"""Abstract interface for spectrum-analyzer devices."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from nfs_scanner.core.models import SpectrumAcquisitionResult, SpectrumConfig


class SpectrumAnalyzer(ABC):
    """Abstract base class for concrete spectrum-analyzer adapters."""

    instrument_type: str = "UNKNOWN"
    resource_name: str = ""

    @abstractmethod
    def connect(self) -> bool:
        """Establish a device connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the device connection."""

    @abstractmethod
    def get_idn(self) -> str:
        """Return the instrument ``*IDN?`` response."""

    @abstractmethod
    def preset(self) -> None:
        """Reset the instrument to one known preset state when supported."""

    @abstractmethod
    def set_center_freq(self, frequency_hz: float) -> None:
        """Apply one center frequency in Hz."""

    @abstractmethod
    def set_span(self, span_hz: float) -> None:
        """Apply one frequency span in Hz."""

    @abstractmethod
    def set_start_stop_freq(self, start_hz: float, stop_hz: float) -> None:
        """Apply one explicit start/stop frequency window in Hz."""

    @abstractmethod
    def set_rbw(self, rbw_hz: float) -> None:
        """Apply one resolution bandwidth in Hz."""

    @abstractmethod
    def set_vbw(self, vbw_hz: float) -> None:
        """Apply one video bandwidth in Hz."""

    @abstractmethod
    def set_ref_level(self, ref_level_dbm: float) -> None:
        """Apply one reference level in dBm."""

    @abstractmethod
    def set_detector(self, detector: str) -> None:
        """Apply one detector mode."""

    @abstractmethod
    def set_trace_mode(self, trace_mode: str) -> None:
        """Apply one trace mode."""

    @abstractmethod
    def set_continuous(self, enabled: bool) -> None:
        """Toggle the instrument continuous acquisition state."""

    @abstractmethod
    def query_setting(self, setting_key: str) -> str:
        """Query one normalized setting key and return the raw SCPI value."""

    @abstractmethod
    def set_setting(self, setting_key: str, value: str | float | int) -> None:
        """Apply one normalized setting key without exposing SCPI to callers."""

    @abstractmethod
    def configure(self, config: SpectrumConfig) -> None:
        """Apply a spectrum acquisition configuration."""

    @abstractmethod
    def trigger_single(self) -> None:
        """Trigger one single-shot acquisition."""

    @abstractmethod
    def wait_opc(self, timeout_ms: int | None = None) -> None:
        """Wait until the instrument reports operation-complete."""

    @abstractmethod
    def fetch_trace(self) -> SpectrumAcquisitionResult:
        """Fetch one trace acquisition payload."""

    @abstractmethod
    def fetch_point_value(self) -> SpectrumAcquisitionResult:
        """Fetch one point-style acquisition payload."""

    @abstractmethod
    def acquire_spectrum(self) -> SpectrumAcquisitionResult:
        """Acquire one spectrum result using the current configuration."""

    def snapshot_configuration(self, setting_keys: Sequence[str]) -> dict[str, str]:
        """Query a normalized configuration snapshot for the given keys."""

        return {setting_key: self.query_setting(setting_key) for setting_key in setting_keys}

    def acquire_trace(self) -> tuple[Sequence[float], Sequence[float]]:
        """Backward-compatible helper returning just axis and trace arrays."""

        return self.acquire_spectrum().to_trace()
