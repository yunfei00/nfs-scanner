"""Tests for scan runtime service protocol compliance."""

from __future__ import annotations

import unittest

from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService
from nfs_scanner.core.runtime_service import ScanRuntimeServiceProtocol
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion


class RuntimeServiceProtocolTestCase(unittest.TestCase):
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

    def test_mock_service_implements_protocol(self) -> None:
        self.assertIsInstance(self.service, ScanRuntimeServiceProtocol)

    def test_configure_sets_configured_status(self) -> None:
        self.service.configure(self.region, self.config)
        snapshot = self.service.snapshot()
        self.assertEqual(snapshot.status, "configured")
        self.assertGreater(snapshot.total_points, 0)

    def test_protocol_lifecycle(self) -> None:
        self.service.configure(self.region, self.config)
        started = self.service.start()
        self.assertEqual(started.status, "running")

        paused = self.service.pause()
        self.assertEqual(paused.status, "paused")

        resumed = self.service.resume()
        self.assertEqual(resumed.status, "running")

        stopped = self.service.stop()
        self.assertEqual(stopped.status, "stopped")

        reset = self.service.reset()
        self.assertIn(reset.status, ("idle", "configured"))


if __name__ == "__main__":
    unittest.main()
