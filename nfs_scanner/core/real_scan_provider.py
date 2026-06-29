"""Real hardware scan provider with safety-gated state machine (tick-based for tests)."""

from __future__ import annotations

import time
from datetime import datetime
from uuid import uuid4

import numpy as np

from nfs_scanner.core.integration_safety import RealDeviceControlBlockedError, require_real_device_control
from nfs_scanner.core.path_planner import generate_snake_points
from nfs_scanner.core.real_scan_models import RealScanProviderResult, RealScanTaskBuffer, ScanPointResult
from nfs_scanner.core.runtime_service import RuntimeSnapshot
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion
from nfs_scanner.core.scan_config_model import PathPlanConfig, ScanConfigModel
from nfs_scanner.core.scan_data_storage import RealScanPointRecord, ScanDataStorage
from nfs_scanner.core.scan_runtime import ScanResultModel, ScanRuntimeState, ScanTaskModel
from nfs_scanner.devices.manager import HardwareDeviceManager


class RealScanProvider:
    """Execute real scans point-by-point via HardwareDeviceManager (no UI thread blocking)."""

    def __init__(self, manager: HardwareDeviceManager) -> None:
        self._manager = manager
        self._state = ScanRuntimeState()
        self._region: ScanRegion | None = None
        self._path_config = ScanPathConfig()
        self._points: list[tuple[float, float, float]] = []
        self._point_index = 0
        self._storage: ScanDataStorage | None = None
        self._buffer = RealScanTaskBuffer(task_id="", task_name="")
        self._settle_delay_ms = 0
        self._project_id = "demo-project"
        self._paused = False
        self._stop_requested = False
        self._started_at = 0.0

    @property
    def state(self) -> ScanRuntimeState:
        return self._state

    @property
    def buffer(self) -> RealScanTaskBuffer:
        return self._buffer

    def snapshot(self) -> RuntimeSnapshot:
        total = len(self._points)
        completed = self._buffer.points.__len__()
        status = self._state.state
        if status == "idle":
            runtime_status = "idle"
        elif status in ("configured", "ready"):
            runtime_status = "configured"
        elif status == "running":
            runtime_status = "running"
        elif status == "paused":
            runtime_status = "paused"
        elif status == "completed":
            runtime_status = "completed"
        elif status == "stopped":
            runtime_status = "stopped"
        else:
            runtime_status = "error"
        elapsed = time.monotonic() - self._started_at if self._started_at else 0.0
        return RuntimeSnapshot(
            status=runtime_status,  # type: ignore[arg-type]
            total_points=total,
            completed_points=completed,
            current_index=self._point_index,
            elapsed_seconds=elapsed,
            last_message=self._state.error_message,
        )

    def configure(self, config: ScanConfigModel) -> RuntimeSnapshot:
        region = config.region
        region.x_step = config.path.step_x
        region.y_step = config.path.step_y
        self._region = region
        self._path_config = config.path.to_path_config()
        self._points = generate_snake_points(region, self._path_config)
        self._point_index = 0
        self._configure_instrument_from_config(config)
        self._state.state = "configured"
        self._state.error_message = ""
        return self.snapshot()

    def configure_region(self, region: ScanRegion, path_config: ScanPathConfig) -> RuntimeSnapshot:
        model = ScanConfigModel(
            region=region,
            path=PathPlanConfig(
                mode=path_config.scan_mode,  # type: ignore[arg-type]
                step_x=region.x_step,
                step_y=region.y_step,
                dwell_ms=path_config.dwell_ms,
                speed_mm_min=path_config.speed_mm_min,
            ),
        )
        return self.configure(model)

    def prepare(self) -> None:
        if self._points:
            self._state.state = "ready"

    def start(self, *, task_name: str | None = None, project_id: str = "demo-project") -> ScanTaskModel:
        try:
            require_real_device_control("scan.start")
        except RealDeviceControlBlockedError as exc:
            self._state.state = "failed"
            self._state.error_message = str(exc)
            raise
        ready, message = self._manager.ensure_ready_for_scan()
        if not ready:
            self._state.state = "failed"
            self._state.error_message = message
            raise RuntimeError(message)
        if not self._points:
            raise RuntimeError("Scan not configured")
        self._project_id = project_id
        self._settle_delay_ms = int(self._manager.config.motion.settle_delay_ms)
        task = ScanTaskModel(
            task_id=f"real-{uuid4().hex[:8]}",
            name=task_name or f"Real Scan {datetime.now().strftime('%H:%M:%S')}",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status="running",
        )
        self._storage = ScanDataStorage(project_id=project_id)
        self._buffer = RealScanTaskBuffer(
            task_id=task.task_id,
            task_name=task.name,
            total_points=len(self._points),
            status="running",
            output_dir=str(self._storage.root),
        )
        self._state.current_task = task
        self._state.state = "running"
        self._state.progress_percent = 0
        self._point_index = 0
        self._paused = False
        self._stop_requested = False
        self._started_at = time.monotonic()
        return task

    def pause(self) -> RuntimeSnapshot:
        self._paused = True
        self._state.state = "paused"
        if self._state.current_task:
            self._state.current_task.status = "paused"
        return self.snapshot()

    def resume(self) -> RuntimeSnapshot:
        self._paused = False
        self._state.state = "running"
        if self._state.current_task:
            self._state.current_task.status = "running"
        return self.snapshot()

    def stop(self) -> ScanResultModel | None:
        self._stop_requested = True
        self._state.state = "stopped"
        try:
            self._manager.motion.stop()
        except Exception:
            pass
        task = self._state.current_task
        if task is None:
            return None
        completed = len(self._buffer.points)
        self._buffer.status = "stopped"
        self._buffer.stopped_by_user = True
        self._finalize_storage(stopped=True)
        result = ScanResultModel(
            task_id=task.task_id,
            completed_points=completed,
            total_points=len(self._points),
            status="stopped",
            completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        task.status = "stopped"
        task.partial = completed > 0
        self._state.last_result = result
        self._state.current_task = None
        return result

    def reset(self) -> RuntimeSnapshot:
        self._points = []
        self._point_index = 0
        self._storage = None
        self._buffer = RealScanTaskBuffer(task_id="", task_name="")
        self._state = ScanRuntimeState()
        return self.snapshot()

    def tick(self) -> RuntimeSnapshot:
        if self._state.state != "running" or self._paused or self._stop_requested:
            return self.snapshot()
        if self._point_index >= len(self._points):
            return self._complete_scan()
        index = self._point_index + 1
        x, y, z = self._points[self._point_index]
        timestamp = datetime.now().isoformat(timespec="seconds")
        motion = self._manager.motion
        instrument = self._manager.instrument
        ok, reason = motion.validate_target_position(x, y, z)
        if not ok:
            self._append_error_point(index, x, y, z, timestamp, reason)
            self._state.state = "failed"
            self._state.error_message = reason
            return self.snapshot()
        try:
            motion.move_absolute(x, y, z)
            if self._settle_delay_ms > 0:
                time.sleep(self._settle_delay_ms / 1000.0)
            acquisition = instrument.measure_at_current_position()
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
            if self._storage is not None:
                self._storage.append_point(record)
            point = ScanPointResult.from_record(
                record,
                instrument_type=instrument.instrument_id,
                resource_name=self._manager.config.instrument.resource,
            )
            self._buffer.append(point)
            self._point_index += 1
            if len(self._points) > 0:
                self._state.progress_percent = int(len(self._buffer.points) / len(self._points) * 100)
        except Exception as exc:
            self._append_error_point(index, x, y, z, timestamp, str(exc))
            self._state.state = "failed"
            self._state.error_message = str(exc)
        if self._point_index >= len(self._points) and self._state.state == "running":
            return self._complete_scan()
        return self.snapshot()

    def complete(self, snapshot: RuntimeSnapshot) -> ScanResultModel:
        task = self._state.current_task
        if task is None:
            task = ScanTaskModel(
                task_id=f"real-{uuid4().hex[:8]}",
                name="Real Scan",
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                status="completed",
            )
        result = ScanResultModel(
            task_id=task.task_id,
            completed_points=snapshot.completed_points,
            total_points=snapshot.total_points,
            status="completed",
            completed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        task.status = "completed"
        self._state.state = "completed"
        self._state.last_result = result
        self._state.progress_percent = 100
        return result

    def provider_result(self) -> RealScanProviderResult | None:
        task = self._state.current_task or (
            ScanTaskModel("", "", "", "stopped") if self._state.last_result else None
        )
        if self._state.last_result is None and not self._buffer.points:
            return None
        last = self._state.last_result
        task_id = last.task_id if last else self._buffer.task_id
        return RealScanProviderResult(
            task_id=task_id,
            completed_points=len(self._buffer.points),
            total_points=len(self._points),
            status=self._buffer.status,
            output_dir=self._buffer.output_dir,
            stopped_by_user=self._buffer.stopped_by_user,
            last_error=self._buffer.last_error,
        )

    def _complete_scan(self) -> RuntimeSnapshot:
        self._buffer.status = "completed"
        self._finalize_storage(stopped=False)
        snap = self.snapshot()
        self.complete(snap)
        self._state.current_task = None
        return snap

    def _finalize_storage(self, *, stopped: bool) -> None:
        if self._storage is None or self._region is None:
            return
        metadata = {
            "project_id": self._project_id,
            "format": "real_scan_result_v1",
            "total_points": len(self._points),
            "completed_points": len(self._buffer.points),
            "stopped_by_user": stopped,
            "last_error": self._buffer.last_error,
        }
        output_dir = self._storage.finalize(metadata)
        self._buffer.output_dir = str(output_dir)

    def _append_error_point(
        self,
        index: int,
        x: float,
        y: float,
        z: float,
        timestamp: str,
        error: str,
    ) -> None:
        record = RealScanPointRecord(
            index=index,
            x_mm=x,
            y_mm=y,
            z_mm=z,
            timestamp=timestamp,
            peak_frequency_hz=0.0,
            peak_amplitude_dbm=0.0,
            status="error",
            error=error,
        )
        if self._storage is not None:
            self._storage.append_point(record)
        self._buffer.last_error = error
        self._buffer.append(
            ScanPointResult.from_record(record, instrument_type=self._manager.instrument.instrument_id)
        )

    def _configure_instrument_from_config(self, config: ScanConfigModel) -> None:
        if not self._manager.instrument.is_connected():
            return
        icfg = self._manager.config.instrument
        try:
            self._manager.instrument.configure_frequency(
                float(icfg.frequency.get("start_hz", 2.4e9)),
                float(icfg.frequency.get("stop_hz", 2.5e9)),
                int(icfg.frequency.get("points", 1001)),
            )
            self._manager.instrument.configure_bandwidth(
                float(icfg.bandwidth.get("rbw_hz", 10000)),
                float(icfg.bandwidth.get("vbw_hz", 10000)),
            )
            self._manager.instrument.configure_trace(icfg.trace_name, "WRIT")
        except Exception as exc:
            self._state.error_message = str(exc)
