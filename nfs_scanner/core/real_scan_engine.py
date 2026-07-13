"""Real hardware scan engine (thread-agnostic core logic)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Literal

import numpy as np

from nfs_scanner.core.path_planner import generate_snake_points
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion
from nfs_scanner.core.scan_data_storage import RealScanPointRecord, ScanDataStorage
from nfs_scanner.devices.instruments.instrument_controller import InstrumentController
from nfs_scanner.devices.motion.base_motion import MotionController


ProgressCallback = Callable[[int, int, RealScanPointRecord], None]
LogCallback = Callable[[str], None]
ScanOutcome = Literal["completed", "stopped", "fast_stopped", "emergency_stopped", "failed"]


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
    outcome: ScanOutcome = "completed"


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
        self._fast_stop_requested = False
        self._emergency_stop_requested = False

    def request_stop(self) -> None:
        """Finish the active safe phase and do not start another scan point."""
        self._stop_requested = True

    def request_fast_stop(self) -> None:
        """Immediately ask motion and instrument adapters to halt current work."""
        self._fast_stop_requested = True
        self._stop_requested = True
        self._stop_devices(emergency=False)

    def emergency_stop(self) -> None:
        """Immediately send the highest-priority stop command to all devices."""
        self._emergency_stop_requested = True
        self._fast_stop_requested = True
        self._stop_requested = True
        self._log("[CRITICAL] Emergency stop requested for real scan")
        self._stop_devices(emergency=True)

    def run(self, config: RealScanConfig) -> RealScanResult:
        points = generate_snake_points(config.region, config.path_config)
        storage = ScanDataStorage(project_id=config.project_id)
        total = len(points)
        completed = 0
        last_error = ""
        outcome: ScanOutcome = "completed"

        for index, (x, y, z) in enumerate(points, start=1):
            requested_outcome = self._requested_outcome()
            if requested_outcome is not None:
                outcome = requested_outcome
                self._log(f"[SCAN] Real scan {outcome} before point {index}")
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
                requested_outcome = self._requested_outcome()
                if requested_outcome is not None:
                    outcome = requested_outcome
                    break
                if not self._wait_settle(config.settle_delay_ms):
                    outcome = self._requested_outcome() or "stopped"
                    break
                requested_outcome = self._requested_outcome()
                if requested_outcome is not None:
                    outcome = requested_outcome
                    break
                acquisition = self._instrument.measure_at_current_position()
                requested_outcome = self._requested_outcome()
                if requested_outcome is not None:
                    outcome = requested_outcome
                    break
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
                requested_outcome = self._requested_outcome()
                if requested_outcome is not None:
                    outcome = requested_outcome
                    break
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
                outcome = "failed"
                break

        if outcome == "completed" and self._requested_outcome() is not None:
            outcome = self._requested_outcome() or "stopped"

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
            "stopped_by_user": outcome in ("stopped", "fast_stopped", "emergency_stopped"),
            "outcome": outcome,
            "last_error": last_error,
            "started_at": datetime.now().isoformat(timespec="seconds"),
        }
        output_dir = storage.finalize(metadata)
        return RealScanResult(
            completed_points=completed,
            total_points=total,
            output_dir=str(output_dir),
            stopped_by_user=outcome in ("stopped", "fast_stopped", "emergency_stopped"),
            last_error=last_error,
            outcome=outcome,
        )

    def _requested_outcome(self) -> ScanOutcome | None:
        if self._emergency_stop_requested:
            return "emergency_stopped"
        if self._fast_stop_requested:
            return "fast_stopped"
        if self._stop_requested:
            return "stopped"
        return None

    def _wait_settle(self, delay_ms: int) -> bool:
        """Wait in short intervals so a stop request is observed during dwell."""
        deadline = time.monotonic() + max(delay_ms, 0) / 1000.0
        while time.monotonic() < deadline:
            if self._requested_outcome() is not None:
                return False
            time.sleep(min(0.05, max(deadline - time.monotonic(), 0.0)))
        return self._requested_outcome() is None

    def _stop_devices(self, *, emergency: bool) -> None:
        try:
            if emergency:
                self._motion.emergency_stop()
            else:
                self._motion.stop()
        except Exception as exc:
            self._log(f"[ERROR] Motion stop command failed: {exc}")
        try:
            self._instrument.abort()
        except Exception as exc:
            self._log(f"[ERROR] Instrument abort command failed: {exc}")

    def _log(self, message: str) -> None:
        if self._on_log is not None:
            self._on_log(message)
