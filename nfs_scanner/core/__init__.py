"""Core application services and data models."""

from .device_manager import DeviceManager
from .device_hub import DeviceHub, DeviceOperationResult
from .models import (
    ScanConfig,
    ScanPointResult,
    SerialConfig,
    SpectrumAcquisitionResult,
    SpectrumConfig,
    SpectrumFrequencySettings,
)
from .scan_manager import ScanManager, ScanRuntimeSnapshot, ScanRuntimeStatus
from .versioning import get_major, is_major_compatible, parse_version, safe_version_str

__all__ = [
    "DeviceManager",
    "DeviceHub",
    "DeviceOperationResult",
    "ScanConfig",
    "ScanPointResult",
    "ScanManager",
    "ScanRuntimeSnapshot",
    "ScanRuntimeStatus",
    "SerialConfig",
    "SpectrumAcquisitionResult",
    "SpectrumConfig",
    "SpectrumFrequencySettings",
    "get_major",
    "is_major_compatible",
    "parse_version",
    "safe_version_str",
]
