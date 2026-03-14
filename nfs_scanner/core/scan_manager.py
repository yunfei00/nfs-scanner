"""Placeholder scan lifecycle manager."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from nfs_scanner.devices import MockCameraDevice, MockMotionController, MockSpectrumAnalyzer

from .models import ScanPointResult, SpectrumConfig


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

    @property
    def is_scanning(self) -> bool:
        """Whether the placeholder scan task is marked as running."""

        return self._is_scanning

    @property
    def results(self) -> list[ScanPointResult]:
        """Return a copy of the most recent in-memory scan results."""

        return list(self._results)

    def start_scan(self) -> bool:
        """Enter placeholder scan-running state."""

        if self._is_scanning:
            self._logger.warning("扫描任务已经处于运行状态。")
            return False

        self._is_scanning = True
        self._logger.info("扫描任务已进入占位运行状态。")
        return True

    def stop_scan(self) -> bool:
        """Leave placeholder scan-running state."""

        if not self._is_scanning:
            self._logger.warning("当前没有运行中的扫描任务。")
            return False

        self._is_scanning = False
        self._logger.info("扫描任务已停止。")
        return True

    def run_grid_scan(self, x_points: Sequence[float], y_points: Sequence[float], z: float) -> list[ScanPointResult]:
        """Run a mock grid scan from explicit point lists."""

        return self._execute_scan(x_points, y_points, z)

    def generate_grid_points(self, config: ScanConfig) -> tuple[list[float], list[float]]:
        """Generate inclusive scan points from a scan configuration."""

        x_points = self._generate_axis_points(config.start_x, config.stop_x, config.step_x)
        if config.scan_mode == "line":
            y_points = [float(config.start_y)]
        elif config.scan_mode == "grid":
            y_points = self._generate_axis_points(config.start_y, config.stop_y, config.step_y)
        else:
            raise ValueError(f"Unsupported scan mode: {config.scan_mode!r}")

        return x_points, y_points

    def run_scan(self, config: ScanConfig) -> list[ScanPointResult]:
        """Run one mock scan from a scan configuration."""

        if self.is_scanning:
            raise RuntimeError("Scan is already running.")

        x_points, y_points = self.generate_grid_points(config)
        total_points = len(x_points) * len(y_points)

        self._logger.info("[SCAN] start scan")
        self._logger.info("[SCAN] total points: %s", total_points)

        results = self._execute_scan(x_points, y_points, config.z_height)
        self._logger.info("[SCAN] scan finished")
        return results

    def _execute_scan(self, x_points: Sequence[float], y_points: Sequence[float], z: float) -> list[ScanPointResult]:
        """Execute one mock scan over explicit axis point lists."""

        if not self.start_scan():
            raise RuntimeError("Scan is already running.")

        self._results = []

        self._motion_controller.connect()
        self._spectrum_analyzer.connect()
        self._camera_device.connect()
        self._spectrum_analyzer.configure(self._spectrum_config)

        try:
            for y_value in y_points:
                for x_value in x_points:
                    x_position = float(x_value)
                    y_position = float(y_value)
                    z_position = float(z)

                    self._logger.info("[SCAN] Move to (%s,%s,%s)", x_position, y_position, z_position)
                    self._motion_controller.move_to(x_position, y_position, z_position)

                    spectrum_trace = self._spectrum_analyzer.acquire_trace()
                    self._logger.info("[SCAN] Spectrum acquired")

                    camera_image = self._camera_device.capture_image()
                    self._logger.info("[SCAN] Image captured")

                    self._results.append(
                        ScanPointResult(
                            x=x_position,
                            y=y_position,
                            z=z_position,
                            spectrum_trace=spectrum_trace,
                            camera_image=camera_image,
                        )
                    )
        finally:
            self._motion_controller.disconnect()
            self._spectrum_analyzer.disconnect()
            self._camera_device.disconnect()
            self.stop_scan()

        return self.results

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

        if not points or points[-1] != round(stop_value, 10):
            points.append(round(stop_value, 10))

        return points
