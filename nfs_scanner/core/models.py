"""Core data models for configuration and scan parameters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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

    start_freq: str = "100MHz"
    stop_freq: str = "3GHz"
    rbw: str = "100kHz"
    lut_name: str = "viridis"
    auto_range: bool = True


@dataclass(slots=True)
class ScanPointResult:
    """One scan-point result containing position, spectrum and image data."""

    x: float
    y: float
    z: float
    spectrum_trace: tuple[NDArray[np.float64], NDArray[np.float64]]
    camera_image: NDArray[np.uint8]
