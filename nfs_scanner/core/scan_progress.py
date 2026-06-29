"""Unified scan point progress payload for Mock and Real scans."""

from __future__ import annotations

from dataclasses import dataclass

from nfs_scanner.core.scan_data_storage import RealScanPointRecord


@dataclass(slots=True)
class ScanPointUpdate:
    """One scan point progress update shared by mock and real workflows."""

    index: int
    total: int
    x_mm: float
    y_mm: float
    z_mm: float
    peak_frequency_hz: float
    peak_amplitude_dbm: float
    timestamp: str
    frequencies_hz: list[float] | None = None
    amplitudes_dbm: list[float] | None = None
    status: str = "ok"
    error: str = ""


def scan_point_update_from_record(current: int, total: int, record: RealScanPointRecord) -> ScanPointUpdate:
    """Convert one RealScanPointRecord into a UI-friendly update payload."""

    return ScanPointUpdate(
        index=current,
        total=total,
        x_mm=record.x_mm,
        y_mm=record.y_mm,
        z_mm=record.z_mm,
        peak_frequency_hz=record.peak_frequency_hz,
        peak_amplitude_dbm=record.peak_amplitude_dbm,
        timestamp=record.timestamp,
        frequencies_hz=record.frequencies_hz,
        amplitudes_dbm=record.amplitudes_dbm,
        status=record.status,
        error=record.error,
    )
