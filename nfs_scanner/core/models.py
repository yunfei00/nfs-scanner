"""Core data models for configuration, acquisition, and scan parameters."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray


@dataclass(slots=True)
class SerialConfig:
    """Serial communication parameters for future motion-control devices."""

    port_name: str = ""
    baud_rate: int = 115200


@dataclass(slots=True)
class ScanConfig:
    """Basic scan-range parameters and traversal strategy."""

    start_x: float = 0.0
    stop_x: float = 100.0
    step_x: float = 1.0
    start_y: float = 0.0
    stop_y: float = 100.0
    step_y: float = 1.0
    z_height: float = 5.0
    scan_mode: Literal["raster", "snake"] = "snake"


@dataclass(slots=True)
class SpectrumConfig:
    """Basic spectrum acquisition and display parameters."""

    start_freq: str | None = "100MHz"
    stop_freq: str | None = "3GHz"
    center_freq: str | None = None
    span: str | None = None
    rbw: str | None = "100kHz"
    vbw: str | None = None
    points: str | int | None = None
    ref_level: str | None = None
    detector: str | None = None
    trace_mode: str | None = None
    fsw_clear_write_delay_seconds: float | None = None
    acquisition_mode: Literal["trace", "point"] = "trace"
    trace_name: str = "TRACE1"
    apply_preset: bool = False
    lut_name: str = "viridis"
    auto_range: bool = True


@dataclass(slots=True)
class SpectrumFrequencySettings:
    """Normalized frequency window information for one acquisition."""

    start_freq_hz: float | None = None
    stop_freq_hz: float | None = None
    center_freq_hz: float | None = None
    span_hz: float | None = None


@dataclass(slots=True)
class SpectrumAcquisitionResult:
    """Normalized spectrum measurement payload returned by instrument adapters."""

    instrument_type: str
    timestamp: datetime
    acquisition_mode: Literal["trace", "point"]
    frequency_settings: SpectrumFrequencySettings = field(default_factory=SpectrumFrequencySettings)
    rbw_hz: float | None = None
    vbw_hz: float | None = None
    ref_level_dbm: float | None = None
    detector: str | None = None
    trace_mode: str | None = None
    trace_frequencies_hz: NDArray[np.float64] | None = None
    trace_values: NDArray[np.float64] | None = None
    point_value: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_trace_data(self) -> bool:
        """Whether this acquisition contains a trace/frequency axis pair."""

        return self.trace_frequencies_hz is not None and self.trace_values is not None

    @property
    def trace_points(self) -> int:
        """Return the trace point count, or zero when no trace is present."""

        if self.trace_values is None:
            return 0
        return int(self.trace_values.size)

    def to_trace(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the normalized trace arrays required by existing scan consumers."""

        if not self.has_trace_data:
            raise ValueError("Spectrum acquisition does not contain trace data.")
        return self.trace_frequencies_hz, self.trace_values

    def to_serializable_dict(self) -> dict[str, Any]:
        """Convert the acquisition payload to a JSON-friendly dictionary."""

        return {
            "instrument_type": self.instrument_type,
            "timestamp": self.timestamp.isoformat(timespec="seconds"),
            "acquisition_mode": self.acquisition_mode,
            "frequency_settings": _to_serializable_value(self.frequency_settings),
            "rbw_hz": self.rbw_hz,
            "vbw_hz": self.vbw_hz,
            "ref_level_dbm": self.ref_level_dbm,
            "detector": self.detector,
            "trace_mode": self.trace_mode,
            "trace_frequencies_hz": _to_serializable_value(self.trace_frequencies_hz),
            "trace_values": _to_serializable_value(self.trace_values),
            "point_value": self.point_value,
            "metadata": _to_serializable_value(self.metadata),
        }


@dataclass(slots=True)
class ScanPointResult:
    """One scan-point result containing position, spectrum and image data."""

    x: float
    y: float
    z: float
    spectrum_trace: tuple[NDArray[np.float64], NDArray[np.float64]]
    camera_image: NDArray[np.uint8]
    spectrum_result: SpectrumAcquisitionResult | None = None


def _to_serializable_value(value: Any) -> Any:
    """Recursively convert common runtime values into JSON-friendly objects."""

    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if is_dataclass(value):
        return {key: _to_serializable_value(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _to_serializable_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_serializable_value(item) for item in value]
    return value
