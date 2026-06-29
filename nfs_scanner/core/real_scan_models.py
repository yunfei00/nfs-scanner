"""Data models for Commercial V1 real scan provider (internal export v1)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from nfs_scanner.core.scan_data_storage import RealScanPointRecord


@dataclass(slots=True)
class ScanPointResult:
    """One measured scan point for UI, export, and report integration."""

    index: int
    x: float
    y: float
    z: float
    timestamp: str
    frequency_axis: list[float]
    trace_values: list[float]
    peak_amplitude: float
    peak_frequency: float
    instrument_type: str = ""
    resource_name: str = ""
    motion_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    status: str = "ok"

    @classmethod
    def from_record(
        cls,
        record: RealScanPointRecord,
        *,
        instrument_type: str = "",
        resource_name: str = "",
    ) -> ScanPointResult:
        frequencies = record.frequencies_hz or []
        amplitudes = record.amplitudes_dbm or []
        return cls(
            index=record.index,
            x=record.x_mm,
            y=record.y_mm,
            z=record.z_mm,
            timestamp=record.timestamp,
            frequency_axis=[float(v) for v in frequencies],
            trace_values=[float(v) for v in amplitudes],
            peak_amplitude=record.peak_amplitude_dbm,
            peak_frequency=record.peak_frequency_hz,
            instrument_type=instrument_type,
            resource_name=resource_name,
            motion_position=(record.x_mm, record.y_mm, record.z_mm),
            status=record.status,
        )


@dataclass
class RealScanTaskBuffer:
    """In-memory buffer for an active or partial real scan task."""

    task_id: str
    task_name: str
    points: list[ScanPointResult] = field(default_factory=list)
    total_points: int = 0
    status: str = "idle"
    output_dir: str = ""
    stopped_by_user: bool = False
    last_error: str = ""

    def append(self, point: ScanPointResult) -> None:
        self.points.append(point)

    def export_json(self, path: Path) -> Path:
        payload: dict[str, Any] = {
            "format": "real_scan_result_v1",
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status,
            "total_points": self.total_points,
            "completed_points": len(self.points),
            "output_dir": self.output_dir,
            "stopped_by_user": self.stopped_by_user,
            "last_error": self.last_error,
            "points": [asdict(point) for point in self.points],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def export_csv(self, path: Path) -> Path:
        import csv

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "index",
                    "x",
                    "y",
                    "z",
                    "timestamp",
                    "peak_frequency_hz",
                    "peak_amplitude_dbm",
                    "status",
                ]
            )
            for point in self.points:
                writer.writerow(
                    [
                        point.index,
                        point.x,
                        point.y,
                        point.z,
                        point.timestamp,
                        point.peak_frequency,
                        point.peak_amplitude,
                        point.status,
                    ]
                )
        return path


@dataclass(slots=True)
class RealScanProviderResult:
    """Final result returned when a real scan completes or stops."""

    task_id: str
    completed_points: int
    total_points: int
    status: str
    output_dir: str
    stopped_by_user: bool = False
    last_error: str = ""
    completed_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
