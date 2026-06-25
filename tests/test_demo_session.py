"""Tests for demo session reset controller."""

from __future__ import annotations

import unittest

from nfs_scanner.core.demo_session import DemoServiceBundle, DemoSessionController
from nfs_scanner.core.dry_run_bundle import create_dry_run_bundle
from nfs_scanner.core.mock_analysis_service import MockAnalysisService
from nfs_scanner.core.mock_device_service import MockDeviceService
from nfs_scanner.core.mock_project_service import MockProjectService
from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService
from nfs_scanner.core.runtime_service import RuntimeSnapshot
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion


class DemoSessionControllerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = MockScanRuntimeService()
        self.dry_run = create_dry_run_bundle()
        self.devices = MockDeviceService()
        self.analysis = MockAnalysisService()
        self.project = MockProjectService()
        self.controller = DemoSessionController()
        self.bundle = DemoServiceBundle(
            runtime=self.runtime,
            dry_run=self.dry_run,
            devices=self.devices,
            analysis=self.analysis,
            project=self.project,
        )

    def test_reset_demo_clears_runtime_and_log(self) -> None:
        self.dry_run.motion.home()
        self.controller.reset_demo(self.bundle, clear_analysis_tasks=False)
        self.assertEqual(len(self.dry_run.log.format_lines()), 0)
        self.assertIn(self.runtime.snapshot().status, ("idle", "configured"))

    def test_reset_demo_restores_default_tasks(self) -> None:
        before = len(self.analysis.list_tasks())
        snapshot = RuntimeSnapshot(status="completed", total_points=9, completed_points=9)
        region = ScanRegion(x_start=0, x_stop=30, y_start=0, y_stop=30, x_step=10, y_step=10)
        config = ScanPathConfig(scan_mode="snake", dwell_ms=100, speed_mm_min=600.0)
        self.analysis.register_completed_mock_scan(snapshot, region, config)
        self.assertGreater(len(self.analysis.list_tasks()), before)
        self.controller.reset_demo(self.bundle, clear_analysis_tasks=True)
        self.assertEqual(len(self.analysis.list_tasks()), 2)


if __name__ == "__main__":
    unittest.main()
