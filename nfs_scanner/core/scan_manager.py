"""Scan lifecycle management and placeholder scan execution services."""

from __future__ import annotations

import logging
import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from nfs_scanner.devices import (
    CameraDevice,
    MockCameraDevice,
    MockMotionController,
    MockSpectrumAnalyzer,
    MotionController,
    SpectrumAnalyzer,
)
from nfs_scanner.scan import ScanJob

from .models import ScanConfig, ScanPointResult, SpectrumConfig

ScanRuntimeStatus = Literal["idle", "running", "paused", "completed", "failed", "stopped"]


@dataclass(slots=True, frozen=True)
class ScanRuntimeSnapshot:
    """Immutable scan runtime data exposed to the UI layer."""

    status: ScanRuntimeStatus = "idle"
    total_points: int = 0
    completed_points: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    elapsed_seconds: float = 0.0
    paused_seconds: float = 0.0
    remaining_seconds: int | None = None
    estimated_completion_time: datetime | None = None
    last_error: str | None = None

    @property
    def progress(self) -> float:
        """Return scan progress as a fraction between 0.0 and 1.0."""

        if self.total_points <= 0:
            return 0.0
        progress = self.completed_points / self.total_points
        return max(0.0, min(1.0, float(progress)))

    @property
    def has_active_scan(self) -> bool:
        """Whether the manager is currently tracking an active scan session."""

        return self.status in {"running", "paused"}


@dataclass(slots=True)
class _ScanRuntimeState:
    """Mutable internal state for scan runtime bookkeeping."""

    status: ScanRuntimeStatus = "idle"
    total_points: int = 0
    completed_points: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    elapsed_seconds: float = 0.0
    paused_seconds: float = 0.0
    run_started_monotonic: float | None = None
    pause_started_monotonic: float | None = None
    remaining_seconds_estimate: int | None = None
    estimated_completion_time: datetime | None = None
    minimum_point_seconds: float = 0.0
    last_error: str | None = None


class ScanManager:
    """Manage scan runtime state and placeholder device-backed scan execution."""

    ACTIVE_SCAN_STATUSES = frozenset({"running", "paused"})

    def __init__(
        self,
        logger: logging.Logger | None = None,
        *,
        motion_controller: MotionController | None = None,
        spectrum_analyzer: SpectrumAnalyzer | None = None,
        camera_device: CameraDevice | None = None,
        now_provider: Callable[[], datetime] | None = None,
        monotonic_provider: Callable[[], float] | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._motion_controller = motion_controller or MockMotionController()
        self._spectrum_analyzer = spectrum_analyzer or MockSpectrumAnalyzer()
        self._camera_device = camera_device or MockCameraDevice()
        self._spectrum_config = SpectrumConfig()
        self._results: list[ScanPointResult] = []
        self._current_job: ScanJob | None = None
        self._runtime = _ScanRuntimeState()
        self._now_provider = now_provider or datetime.now
        self._monotonic_provider = monotonic_provider or time.monotonic

    @property
    def is_scanning(self) -> bool:
        """Whether a scan is actively running."""

        return self._runtime.status == "running"

    @property
    def current_job(self) -> ScanJob | None:
        """Return the current or most recent scan job."""

        return self._current_job

    @property
    def results(self) -> list[ScanPointResult]:
        """Return a copy of the most recent in-memory scan results."""

        return list(self._results)

    @property
    def scan_runtime_snapshot(self) -> ScanRuntimeSnapshot:
        """Return the current runtime state snapshot."""

        return self.get_scan_runtime_snapshot()

    def get_scan_runtime_snapshot(self) -> ScanRuntimeSnapshot:
        """Build one immutable snapshot for the current scan runtime state."""

        return ScanRuntimeSnapshot(
            status=self._runtime.status,
            total_points=self._runtime.total_points,
            completed_points=self._runtime.completed_points,
            started_at=self._runtime.started_at,
            finished_at=self._runtime.finished_at,
            elapsed_seconds=self._get_elapsed_scan_seconds(),
            paused_seconds=self._get_paused_seconds(),
            remaining_seconds=self._get_display_remaining_seconds(),
            estimated_completion_time=self._runtime.estimated_completion_time,
            last_error=self._runtime.last_error,
        )

    def begin_scan(
        self,
        total_points: int,
        *,
        minimum_point_seconds: float = 0.0,
        scan_config: ScanConfig | None = None,
        job: ScanJob | None = None,
    ) -> ScanRuntimeSnapshot:
        """Start one new scan runtime session."""

        if self._runtime.status in self.ACTIVE_SCAN_STATUSES:
            raise RuntimeError("Scan is already running.")

        normalized_total_points = max(int(total_points), 0)
        self._runtime = _ScanRuntimeState(
            status="running",
            total_points=normalized_total_points,
            started_at=self._now_provider(),
            run_started_monotonic=self._monotonic_provider(),
            minimum_point_seconds=max(float(minimum_point_seconds), 0.0),
        )

        if job is not None:
            self._current_job = job
        elif scan_config is not None:
            self._current_job = self._create_job(scan_config)
        else:
            self._current_job = None

        if self._current_job is not None:
            self._current_job.mark_running()
            self._sync_current_job_progress()

        self._update_remaining_time_estimate()
        self._logger.info("[SCAN] runtime entered running state")
        return self.get_scan_runtime_snapshot()

    def start_scan(self) -> bool:
        """Legacy boolean API for entering a placeholder running state."""

        try:
            self.begin_scan(total_points=0)
        except RuntimeError:
            self._logger.warning("Scan task is already running.")
            return False

        self._logger.info("Scan task entered running state.")
        return True

    def pause_scan(self) -> ScanRuntimeSnapshot:
        """Pause the active scan session and freeze ETA updates."""

        if self._runtime.status != "running":
            raise RuntimeError("No active running scan task to pause.")

        self._freeze_remaining_time_estimate()
        self._accumulate_elapsed_seconds()
        self._runtime.pause_started_monotonic = self._monotonic_provider()
        self._runtime.status = "paused"
        if self._current_job is not None:
            self._current_job.pause()
        self._logger.info("[SCAN] runtime paused")
        return self.get_scan_runtime_snapshot()

    def resume_scan(self) -> ScanRuntimeSnapshot:
        """Resume one paused scan session."""

        if self._runtime.status != "paused":
            raise RuntimeError("No paused scan task to resume.")

        self._accumulate_paused_seconds()
        self._runtime.run_started_monotonic = self._monotonic_provider()
        self._runtime.status = "running"
        if self._runtime.remaining_seconds_estimate is not None:
            self._runtime.estimated_completion_time = self._now_provider() + timedelta(
                seconds=self._runtime.remaining_seconds_estimate
            )
        if self._current_job is not None:
            self._current_job.resume()
        self._logger.info("[SCAN] runtime resumed")
        return self.get_scan_runtime_snapshot()

    def record_completed_point(self, points: int = 1) -> ScanRuntimeSnapshot:
        """Record completed scan points and update ETA estimation."""

        if self._runtime.status != "running":
            raise RuntimeError("Cannot update scan progress when no scan is running.")

        normalized_points = max(int(points), 0)
        if normalized_points > 0:
            self._runtime.completed_points = min(
                self._runtime.completed_points + normalized_points,
                self._runtime.total_points,
            )
            self._sync_current_job_progress()
        self._update_remaining_time_estimate()
        return self.get_scan_runtime_snapshot()

    def complete_scan(self) -> ScanRuntimeSnapshot:
        """Mark the active scan session as completed."""

        if self._runtime.status == "running":
            self._accumulate_elapsed_seconds()
        elif self._runtime.status == "paused":
            self._accumulate_paused_seconds()

        finished_at = self._now_provider()
        self._runtime.status = "completed"
        self._runtime.finished_at = finished_at
        self._runtime.completed_points = self._runtime.total_points
        self._runtime.last_error = None
        self._set_remaining_time_estimate(0, now_value=finished_at)
        if self._current_job is not None:
            self._current_job.mark_completed()
        self._logger.info("[SCAN] runtime completed")
        return self.get_scan_runtime_snapshot()

    def fail_scan(self, reason: str | None = None) -> ScanRuntimeSnapshot:
        """Mark the scan session as failed and clear ETA data."""

        if self._runtime.status == "running":
            self._accumulate_elapsed_seconds()
        elif self._runtime.status == "paused":
            self._accumulate_paused_seconds()

        self._runtime.status = "failed"
        self._runtime.finished_at = self._now_provider()
        self._runtime.last_error = reason
        self._clear_remaining_time_estimate()
        if self._current_job is not None:
            self._current_job.mark_failed()
        self._logger.info("[SCAN] runtime failed")
        return self.get_scan_runtime_snapshot()

    def stop_scan(self) -> bool:
        """Stop the active scan session and reset timing display state."""

        if self._runtime.status not in self.ACTIVE_SCAN_STATUSES:
            self._logger.warning("No active scan task is running.")
            return False

        finished_at = self._now_provider()
        if self._current_job is not None:
            self._current_job.mark_stopped()
        self._runtime = _ScanRuntimeState(status="stopped", finished_at=finished_at)
        self._logger.info("Scan task stopped.")
        return True

    def get_motion_axis_limits(self) -> dict[str, tuple[float, float]]:
        """Return the current motion-axis limits for UI display and validation."""

        return self._motion_controller.get_axis_limits()

    def move_to_position(self, x: float, y: float, z: float) -> tuple[bool, str]:
        """Execute one manual move command if the target position is in range."""

        target_x = float(x)
        target_y = float(y)
        target_z = float(z)
        is_valid, reason = self._motion_controller.validate_target(target_x, target_y, target_z)
        if not is_valid:
            return False, reason

        self._motion_controller.connect()
        try:
            self._motion_controller.move_to(target_x, target_y, target_z)
        finally:
            self._motion_controller.disconnect()

        return True, ""

    def run_grid_scan(
        self,
        x_points: Sequence[float],
        y_points: Sequence[float],
        z: float,
        scan_mode: Literal["raster", "snake"] = "snake",
        on_point_acquired: Callable[[ScanPointResult], None] | None = None,
        on_job_updated: Callable[[ScanJob], None] | None = None,
    ) -> list[ScanPointResult]:
        """Run a mock grid scan from explicit point lists."""

        if self.scan_runtime_snapshot.has_active_scan:
            raise RuntimeError("Scan is already running.")

        scan_config = self._build_scan_config_from_points(x_points, y_points, z, scan_mode)
        scan_points = self._select_scan_points(x_points, y_points, scan_mode)
        return self._run_scan_job(
            scan_config,
            scan_points,
            scan_config.z_height,
            on_point_acquired,
            on_job_updated,
        )

    def generate_grid_points(self, config: ScanConfig) -> tuple[list[float], list[float]]:
        """Generate inclusive axis point lists from a scan configuration."""

        x_points = self._generate_axis_points(config.start_x, config.stop_x, config.step_x)
        y_points = self._generate_axis_points(config.start_y, config.stop_y, config.step_y)
        return x_points, y_points

    def run_scan(
        self,
        config: ScanConfig,
        on_point_acquired: Callable[[ScanPointResult], None] | None = None,
        on_job_updated: Callable[[ScanJob], None] | None = None,
    ) -> list[ScanPointResult]:
        """Run one mock scan from a scan configuration."""

        if self.scan_runtime_snapshot.has_active_scan:
            raise RuntimeError("Scan is already running.")

        x_points, y_points = self.generate_grid_points(config)
        scan_points = self._select_scan_points(x_points, y_points, config.scan_mode)
        return self._run_scan_job(
            config,
            scan_points,
            config.z_height,
            on_point_acquired,
            on_job_updated,
        )

    def generate_snake_scan_points(
        self,
        x_points: Sequence[float],
        y_points: Sequence[float],
    ) -> list[tuple[float, float]]:
        """Generate a snake-style scan path from X and Y axis points."""

        normalized_x_points = [float(value) for value in x_points]
        normalized_y_points = [float(value) for value in y_points]
        scan_points: list[tuple[float, float]] = []

        for row_index, y_value in enumerate(normalized_y_points):
            row_x_points = normalized_x_points if row_index % 2 == 0 else list(reversed(normalized_x_points))
            scan_points.extend((x_value, y_value) for x_value in row_x_points)

        return scan_points

    def generate_raster_scan_points(
        self,
        x_points: Sequence[float],
        y_points: Sequence[float],
    ) -> list[tuple[float, float]]:
        """Generate a traditional row-major raster scan path."""

        normalized_x_points = [float(value) for value in x_points]
        normalized_y_points = [float(value) for value in y_points]
        return [(x_value, y_value) for y_value in normalized_y_points for x_value in normalized_x_points]

    def _run_scan_job(
        self,
        config: ScanConfig,
        scan_points: Sequence[tuple[float, float]],
        z: float,
        on_point_acquired: Callable[[ScanPointResult], None] | None = None,
        on_job_updated: Callable[[ScanJob], None] | None = None,
    ) -> list[ScanPointResult]:
        """Create one scan job and execute it over an explicit path."""

        job = self._create_job(config)
        self._notify_job_updated(job, on_job_updated)
        total_points = len(scan_points)

        self._logger.info("[SCAN] start scan")
        self._logger.info("[SCAN] mode=%s", config.scan_mode)
        self._logger.info("[SCAN] total points: %s", total_points)

        results = self._execute_scan_points(
            job,
            scan_points,
            z,
            on_point_acquired=on_point_acquired,
            on_job_updated=on_job_updated,
        )
        self._logger.info("[SCAN] scan finished")
        return results

    def _create_job(self, config: ScanConfig) -> ScanJob:
        """Create and store one scan job for the current execution."""

        self._current_job = ScanJob(scan_config=config)
        self._logger.info("[SCAN] job created")
        return self._current_job

    def _execute_scan_points(
        self,
        job: ScanJob,
        scan_points: Sequence[tuple[float, float]],
        z: float,
        *,
        on_point_acquired: Callable[[ScanPointResult], None] | None = None,
        on_job_updated: Callable[[ScanJob], None] | None = None,
    ) -> list[ScanPointResult]:
        """Execute one mock scan over an explicit XY scan path."""

        total_points = len(scan_points)
        self.begin_scan(total_points=total_points, job=job)
        self._results = []

        try:
            self._motion_controller.connect()
            self._spectrum_analyzer.connect()
            self._camera_device.connect()
            self._spectrum_analyzer.configure(self._spectrum_config)
            self._logger.info("[SCAN] job started")
            self._notify_job_updated(job, on_job_updated)

            for x_value, y_value in scan_points:
                x_position = float(x_value)
                y_position = float(y_value)
                z_position = float(z)

                self._logger.info("[SCAN] move (%s,%s)", x_position, y_position)
                self._motion_controller.move_to(x_position, y_position, z_position)

                spectrum_trace = self._spectrum_analyzer.acquire_trace()
                self._logger.info("[SCAN] Spectrum acquired")

                camera_image = self._camera_device.capture_image()
                self._logger.info("[SCAN] Image captured")

                point_result = ScanPointResult(
                    x=x_position,
                    y=y_position,
                    z=z_position,
                    spectrum_trace=spectrum_trace,
                    camera_image=camera_image,
                )
                self._results.append(point_result)
                self.record_completed_point()
                self._notify_job_updated(job, on_job_updated)
                self._logger.info("[SCAN] point acquired (%s,%s)", x_position, y_position)

                if on_point_acquired is not None:
                    on_point_acquired(point_result)
        except Exception as error:
            self.fail_scan(str(error))
            self._logger.info("[SCAN] job failed")
            self._notify_job_updated(job, on_job_updated)
            raise
        else:
            self.complete_scan()
            self._logger.info("[SCAN] job completed")
            self._notify_job_updated(job, on_job_updated)
        finally:
            self._motion_controller.disconnect()
            self._spectrum_analyzer.disconnect()
            self._camera_device.disconnect()

        return self.results

    def _select_scan_points(
        self,
        x_points: Sequence[float],
        y_points: Sequence[float],
        scan_mode: Literal["raster", "snake"],
    ) -> list[tuple[float, float]]:
        """Select one traversal strategy for the current scan."""

        if scan_mode == "snake":
            return self.generate_snake_scan_points(x_points, y_points)
        if scan_mode == "raster":
            return self.generate_raster_scan_points(x_points, y_points)
        raise ValueError(f"Unsupported scan mode: {scan_mode!r}")

    def _generate_axis_points(self, start: float, stop: float, step: float) -> list[float]:
        """Generate an inclusive point list for one scan axis."""

        start_value = float(start)
        stop_value = float(stop)
        step_value = float(step)

        if step_value <= 0.0:
            raise ValueError("Scan step must be greater than zero.")
        if stop_value < start_value:
            raise ValueError("Scan stop must be greater than or equal to scan start.")

        points: list[float] = []
        current = start_value
        epsilon = step_value * 1.0e-9
        while current <= stop_value + epsilon:
            points.append(round(current, 10))
            current += step_value

        rounded_stop = round(stop_value, 10)
        if not points or points[-1] != rounded_stop:
            points.append(rounded_stop)

        return points

    def _build_scan_config_from_points(
        self,
        x_points: Sequence[float],
        y_points: Sequence[float],
        z: float,
        scan_mode: Literal["raster", "snake"],
    ) -> ScanConfig:
        """Build a best-effort scan config from explicit axis point lists."""

        normalized_x_points = [float(value) for value in x_points]
        normalized_y_points = [float(value) for value in y_points]

        return ScanConfig(
            start_x=normalized_x_points[0] if normalized_x_points else 0.0,
            stop_x=normalized_x_points[-1] if normalized_x_points else 0.0,
            step_x=self._infer_step(normalized_x_points),
            start_y=normalized_y_points[0] if normalized_y_points else 0.0,
            stop_y=normalized_y_points[-1] if normalized_y_points else 0.0,
            step_y=self._infer_step(normalized_y_points),
            z_height=float(z),
            scan_mode=scan_mode,
        )

    def _infer_step(self, points: Sequence[float]) -> float:
        """Infer one axis step from an explicit point list."""

        if len(points) < 2:
            return 1.0
        return abs(float(points[1]) - float(points[0])) or 1.0

    def _notify_job_updated(
        self,
        job: ScanJob,
        callback: Callable[[ScanJob], None] | None,
    ) -> None:
        """Notify one observer that the current job changed."""

        if callback is not None:
            callback(job)

    def _sync_current_job_progress(self) -> None:
        """Sync the current job object with runtime progress when available."""

        if self._current_job is None:
            return
        self._current_job.update_progress(self._runtime.completed_points, self._runtime.total_points)

    def _update_remaining_time_estimate(self) -> None:
        """Update the current remaining-time estimate for the runtime state."""

        if self._runtime.status != "running":
            return
        if self._runtime.total_points <= 0:
            self._clear_remaining_time_estimate()
            return

        remaining_points = max(self._runtime.total_points - self._runtime.completed_points, 0)
        if remaining_points == 0:
            self._set_remaining_time_estimate(0)
            return

        avg_seconds_per_point = self._get_estimated_seconds_per_point()
        if avg_seconds_per_point is None:
            self._clear_remaining_time_estimate()
            return

        remaining_seconds = math.ceil(avg_seconds_per_point * remaining_points)
        self._set_remaining_time_estimate(remaining_seconds)

    def _get_estimated_seconds_per_point(self) -> float | None:
        """Estimate the average time spent per completed scan point."""

        minimum_seconds = max(self._runtime.minimum_point_seconds, 0.0)
        if self._runtime.completed_points <= 0:
            return minimum_seconds or None

        elapsed_seconds = self._get_elapsed_scan_seconds()
        if elapsed_seconds <= 0:
            return minimum_seconds or None
        return max(elapsed_seconds / self._runtime.completed_points, minimum_seconds)

    def _set_remaining_time_estimate(
        self,
        remaining_seconds: int | None,
        *,
        now_value: datetime | None = None,
    ) -> None:
        """Store one ETA estimate for the current runtime state."""

        if remaining_seconds is None:
            self._runtime.remaining_seconds_estimate = None
            self._runtime.estimated_completion_time = None
            return

        normalized_seconds = max(int(remaining_seconds), 0)
        anchor_time = now_value or self._now_provider()
        self._runtime.remaining_seconds_estimate = normalized_seconds
        self._runtime.estimated_completion_time = anchor_time + timedelta(seconds=normalized_seconds)

    def _clear_remaining_time_estimate(self) -> None:
        """Clear the stored ETA estimate."""

        self._set_remaining_time_estimate(None)

    def _freeze_remaining_time_estimate(self) -> None:
        """Freeze the current running ETA before transitioning to paused."""

        self._runtime.remaining_seconds_estimate = self._get_display_remaining_seconds()
        if self._runtime.remaining_seconds_estimate is None:
            self._runtime.estimated_completion_time = None

    def _get_display_remaining_seconds(self) -> int | None:
        """Return the remaining seconds that should currently be shown in the UI."""

        remaining_seconds = self._runtime.remaining_seconds_estimate
        if remaining_seconds is None:
            return None
        if self._runtime.status != "running" or self._runtime.estimated_completion_time is None:
            return remaining_seconds

        dynamic_remaining = math.ceil(
            (self._runtime.estimated_completion_time - self._now_provider()).total_seconds()
        )
        return max(dynamic_remaining, 0)

    def _accumulate_elapsed_seconds(self) -> None:
        """Persist the current running segment into elapsed scan time."""

        if self._runtime.run_started_monotonic is None:
            return

        self._runtime.elapsed_seconds = self._get_elapsed_scan_seconds()
        self._runtime.run_started_monotonic = None

    def _accumulate_paused_seconds(self) -> None:
        """Persist the current pause segment into total paused time."""

        if self._runtime.pause_started_monotonic is None:
            return

        self._runtime.paused_seconds = self._get_paused_seconds()
        self._runtime.pause_started_monotonic = None

    def _get_elapsed_scan_seconds(self) -> float:
        """Return accumulated active scan runtime in seconds."""

        elapsed_seconds = self._runtime.elapsed_seconds
        if self._runtime.run_started_monotonic is not None:
            elapsed_seconds += max(self._monotonic_provider() - self._runtime.run_started_monotonic, 0.0)
        return max(elapsed_seconds, 0.0)

    def _get_paused_seconds(self) -> float:
        """Return accumulated paused runtime in seconds."""

        paused_seconds = self._runtime.paused_seconds
        if self._runtime.pause_started_monotonic is not None:
            paused_seconds += max(self._monotonic_provider() - self._runtime.pause_started_monotonic, 0.0)
        return max(paused_seconds, 0.0)
