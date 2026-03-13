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
        """Run a mock grid scan and store all point results in memory."""

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
