"""Tests for mock scan runtime service."""

from __future__ import annotations

import unittest

from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion


class MockScanRuntimeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._clock = 0.0
        self.service = MockScanRuntimeService(monotonic_provider=lambda: self._clock)
        self.region = ScanRegion(
            x_start=0.0,
            x_stop=10.0,
            y_start=0.0,
            y_stop=10.0,
            x_step=5.0,
            y_step=5.0,
        )
        self.config = ScanPathConfig(scan_mode="snake", dwell_ms=10, speed_mm_min=600.0)
        self.service.configure(self.region, self.config)

    def test_start_and_complete_via_ticks(self) -> None:
        snapshot = self.service.start()
        self.assertEqual(snapshot.status, "running")
        self.assertGreater(snapshot.total_points, 0)

        while snapshot.status == "running":
            self._clock += 0.05
            snapshot = self.service.tick()
        self.assertEqual(snapshot.status, "completed")
        self.assertEqual(snapshot.completed_points, snapshot.total_points)

    def test_pause_and_resume(self) -> None:
        self.service.start()
        self.service.tick()
        paused = self.service.pause()
        self.assertEqual(paused.status, "paused")
        stuck = self.service.tick()
        self.assertEqual(stuck.completed_points, 1)
        resumed = self.service.resume()
        self.assertEqual(resumed.status, "running")

    def test_stop_aborts_running_scan(self) -> None:
        self.service.start()
        self.service.tick()
        stopped = self.service.stop()
        self.assertEqual(stopped.status, "stopped")

    def test_configure_before_start(self) -> None:
        configured = self.service.snapshot()
        self.assertEqual(configured.status, "configured")


if __name__ == "__main__":
    unittest.main()
