"""Core data models for configuration and scan parameters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SerialConfig:
    """Serial communication parameters for future motion-control devices."""

    port_name: str = ""
    baud_rate: int = 115200


@dataclass(slots=True)
class ScanConfig:
    """Basic scan-range parameters."""

    start_x: float = 0.0
    stop_x: float = 100.0
    step_x: float = 1.0
    start_y: float = 0.0
    stop_y: float = 100.0
    step_y: float = 1.0


@dataclass(slots=True)
class SpectrumConfig:
    """Basic spectrum acquisition and display parameters."""

    device_type: str = "频谱仪"
    start_freq_hz: float = 1.0e9
    stop_freq_hz: float = 6.0e9
    rbw_hz: float = 1.0e5
    lut: str = "Viridis"
    auto_range: bool = True
