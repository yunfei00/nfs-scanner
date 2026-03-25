"""Placeholder scan lifecycle manager."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import Literal

from nfs_scanner.devices import MockCameraDevice, MockMotionController, MockSpectrumAnalyzer
from nfs_scanner.scan import ScanJob

from .models import ScanConfig, ScanPointResult, SpectrumConfig


class ScanManager:
    """Manage the scan task lifecycle using mock devices."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._is_scanning = False
        self._motion_controller = MockMotionController()
        self._spectrum_analyzer = MockSpectrumAnalyzer()
        self._camera_device = MockCameraDevice()
        self._spectrum_config = SpectrumConfig()
        self._results: list[ScanPointResult] = []
        self._current_job: ScanJob | None = None

    @property
    def is_scanning(self) -> bool:
        """Whether the placeholder scan task is marked as running."""

        return self._is_scanning

    @property
    def results(self) -> list[ScanPointResult]:
        """Return a copy of the most recent in-memory scan results."""

        return list(self._results)

    @property
    def current_job(self) -> ScanJob | None:
        """Return the current or most recent scan job."""

        return self._current_job

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

    def start_scan(self) -> bool:
        """Enter placeholder scan-running state."""

        if self._is_scanning:
            self._logger.warning("Scan task is already running.")
            return False

        self._is_scanning = True
        self._logger.info("Scan task entered running state.")
        return True

    def stop_scan(self) -> bool:
        """Leave placeholder scan-running state."""

        if not self._is_scanning:
            self._logger.warning("No active scan task is running.")
            return False

        self._is_scanning = False
        self._logger.info("Scan task stopped.")
        return True

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

        if self.is_scanning:
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

        if self.is_scanning:
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

        if not self.start_scan():
            raise RuntimeError("Scan is already running.")

        self._results = []
        total_points = len(scan_points)

        self._motion_controller.connect()
        self._spectrum_analyzer.connect()
        self._camera_device.connect()
        self._spectrum_analyzer.configure(self._spectrum_config)
        job.mark_running()
        self._logger.info("[SCAN] job started")
        self._notify_job_updated(job, on_job_updated)

        try:
            for point_index, (x_value, y_value) in enumerate(scan_points, start=1):
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
                job.update_progress(point_index, total_points)
                self._notify_job_updated(job, on_job_updated)
                self._logger.info("[SCAN] point acquired (%s,%s)", x_position, y_position)

                if on_point_acquired is not None:
                    on_point_acquired(point_result)
        except Exception:
            job.mark_failed()
            self._logger.info("[SCAN] job failed")
            self._notify_job_updated(job, on_job_updated)
            raise
        else:
            job.mark_completed()
            self._logger.info("[SCAN] job completed")
            self._notify_job_updated(job, on_job_updated)
        finally:
            self._motion_controller.disconnect()
            self._spectrum_analyzer.disconnect()
            self._camera_device.disconnect()
            self.stop_scan()

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
