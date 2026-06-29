"""Real hardware scan engine (thread-agnostic core logic)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

import numpy as np

from nfs_scanner.core.path_planner import generate_snake_points
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion
from nfs_scanner.core.scan_data_storage import RealScanPointRecord, ScanDataStorage
from nfs_scanner.devices.instruments.instrument_controller import InstrumentController
from nfs_scanner.devices.motion.base_motion import MotionController


ProgressCallback = Callable[[int, int, RealScanPointRecord], None]
LogCallback = Callable[[str], None]


@dataclass(slots=True)
class RealScanConfig:
    region: ScanRegion
    path_config: ScanPathConfig = field(default_factory=ScanPathConfig)
    settle_delay_ms: int = 200
    project_id: str = "demo-project"


@dataclass(slots=True)
class RealScanResult:
    completed_points: int
    total_points: int
    output_dir: str
    stopped_by_user: bool = False
    last_error: str = ""


class RealScanEngine:
    """Execute one real scan over snake path points."""

    def __init__(
        self,
        *,
        motion: MotionController,
        instrument: InstrumentController,
        on_progress: ProgressCallback | None = None,
        on_log: LogCallback | None = None,
    ) -> None:
        self._motion = motion
        self._instrument = instrument
        self._on_progress = on_progress
        self._on_log = on_log
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    def run(self, config: RealScanConfig) -> RealScanResult:
        points = generate_snake_points(config.region, config.path_config)
        storage = ScanDataStorage(project_id=config.project_id)
        total = len(points)
        completed = 0
        last_error = ""

        for index, (x, y, z) in enumerate(points, start=1):
            if self._stop_requested:
                self._log("[SCAN] Real scan stopped by user")
                try:
                    self._motion.stop()
                except Exception:
                    pass
                try:
                    self._instrument.abort()
                except Exception:
                    pass
                break

            timestamp = datetime.now().isoformat(timespec="seconds")
            ok, reason = self._motion.validate_target_position(x, y, z)
            if not ok:
                record = RealScanPointRecord(
                    index=index,
                    x_mm=x,
                    y_mm=y,
                    z_mm=z,
                    timestamp=timestamp,
                    peak_frequency_hz=0.0,
                    peak_amplitude_dbm=0.0,
                    status="error",
                    error=reason,
                )
                storage.append_point(record)
                last_error = reason
                self._log(f"[ERROR] {reason}")
                break

            try:
                self._motion.move_absolute(x, y, z)
                if config.settle_delay_ms > 0:
                    time.sleep(config.settle_delay_ms / 1000.0)
                acquisition = self._instrument.measure_at_current_position()
                frequencies, amplitudes = acquisition.to_trace()
                peak_index = int(np.argmax(amplitudes)) if len(amplitudes) else 0
                record = RealScanPointRecord(
                    index=index,
                    x_mm=x,
                    y_mm=y,
                    z_mm=z,
                    timestamp=timestamp,
                    peak_frequency_hz=float(frequencies[peak_index]) if len(frequencies) else 0.0,
                    peak_amplitude_dbm=float(amplitudes[peak_index]) if len(amplitudes) else 0.0,
                    frequencies_hz=[float(v) for v in frequencies],
                    amplitudes_dbm=[float(v) for v in amplitudes],
                )
                storage.append_point(record)
                completed = index
                self._log(f"[SCAN] point {index}/{total} X={x:.2f} Y={y:.2f}")
                if self._on_progress is not None:
                    self._on_progress(index, total, record)
            except Exception as exc:
                last_error = str(exc)
                storage.append_point(
                    RealScanPointRecord(
                        index=index,
                        x_mm=x,
                        y_mm=y,
                        z_mm=z,
                        timestamp=timestamp,
                        peak_frequency_hz=0.0,
                        peak_amplitude_dbm=0.0,
                        status="error",
                        error=last_error,
                    )
                )
                self._log(f"[ERROR] Real scan failed at point {index}: {last_error}")
                break

        metadata = {
            "project_id": config.project_id,
            "scan_area": {
                "x_start": config.region.x_start,
                "x_stop": config.region.x_stop,
                "y_start": config.region.y_start,
                "y_stop": config.region.y_stop,
                "z_height": config.region.z_height,
                "x_step": config.region.x_step,
                "y_step": config.region.y_step,
            },
            "total_points": total,
            "completed_points": completed,
            "stopped_by_user": self._stop_requested,
            "last_error": last_error,
            "started_at": datetime.now().isoformat(timespec="seconds"),
        }
        output_dir = storage.finalize(metadata)
        return RealScanResult(
            completed_points=completed,
            total_points=total,
            output_dir=str(output_dir),
            stopped_by_user=self._stop_requested,
            last_error=last_error,
        )

    def _log(self, message: str) -> None:
        if self._on_log is not None:
            self._on_log(message)
