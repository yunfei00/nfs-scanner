"""Persist real scan outputs under outputs/scans/."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from nfs_scanner.core.output_paths import OUTPUT_ROOT


@dataclass(slots=True)
class RealScanPointRecord:
    index: int
    x_mm: float
    y_mm: float
    z_mm: float
    timestamp: str
    peak_frequency_hz: float
    peak_amplitude_dbm: float
    status: str = "ok"
    error: str = ""
    frequencies_hz: list[float] | None = None
    amplitudes_dbm: list[float] | None = None


class ScanDataStorage:
    """Write scan_points.csv, traces.npz and metadata.json for one run."""

    def __init__(self, *, project_id: str, base_dir: Path | None = None) -> None:
        token = datetime.now().strftime("%Y%m%d_%H%M%S")
        root = base_dir or (OUTPUT_ROOT / "scans" / project_id / token)
        root.mkdir(parents=True, exist_ok=True)
        self.root = root
        self._points_path = root / "scan_points.csv"
        self._metadata_path = root / "metadata.json"
        self._log_path = root / "run.log"
        self._trace_indices: list[int] = []
        self._trace_x: list[float] = []
        self._trace_y: list[float] = []
        self._trace_z: list[float] = []
        self._frequencies: list[np.ndarray] = []
        self._amplitudes: list[np.ndarray] = []
        self._init_csv()

    @property
    def points_csv_path(self) -> Path:
        return self._points_path

    @property
    def metadata_path(self) -> Path:
        return self._metadata_path

    def append_log(self, line: str) -> None:
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(line.rstrip() + "\n")

    def append_point(self, record: RealScanPointRecord) -> None:
        with self._points_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    record.index,
                    record.x_mm,
                    record.y_mm,
                    record.z_mm,
                    record.timestamp,
                    record.peak_frequency_hz,
                    record.peak_amplitude_dbm,
                    record.status,
                    record.error,
                ]
            )
        if record.frequencies_hz and record.amplitudes_dbm:
            self._trace_indices.append(record.index)
            self._trace_x.append(record.x_mm)
            self._trace_y.append(record.y_mm)
            self._trace_z.append(record.z_mm)
            self._frequencies.append(np.asarray(record.frequencies_hz, dtype=np.float64))
            self._amplitudes.append(np.asarray(record.amplitudes_dbm, dtype=np.float64))

    def finalize(self, metadata: dict[str, Any]) -> Path:
        self._metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        if self._frequencies:
            np.savez_compressed(
                self.root / "traces.npz",
                index=np.asarray(self._trace_indices, dtype=np.int32),
                x_mm=np.asarray(self._trace_x, dtype=np.float64),
                y_mm=np.asarray(self._trace_y, dtype=np.float64),
                z_mm=np.asarray(self._trace_z, dtype=np.float64),
                frequencies_hz=np.array(self._frequencies, dtype=object),
                amplitudes_dbm=np.array(self._amplitudes, dtype=object),
            )
        return self.root

    def _init_csv(self) -> None:
        with self._points_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "index",
                    "x_mm",
                    "y_mm",
                    "z_mm",
                    "timestamp",
                    "peak_frequency_hz",
                    "peak_amplitude_dbm",
                    "status",
                    "error",
                ]
            )
