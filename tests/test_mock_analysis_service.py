"""Tests for mock analysis service."""

from __future__ import annotations

import unittest

from nfs_scanner.core.mock_analysis_service import MockAnalysisService
from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeSnapshot
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion


class MockAnalysisServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.service = MockAnalysisService()

    def test_list_default_tasks(self) -> None:
        tasks = self.service.list_tasks()
        self.assertGreaterEqual(len(tasks), 2)

    def test_build_summary_for_task(self) -> None:
        task_id = self.service.list_tasks()[0].task_id
        summary = self.service.build_summary(task_id, view_mode="frequency")
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.view_mode, "frequency")

    def test_register_completed_mock_scan(self) -> None:
        snapshot = MockScanRuntimeSnapshot(
            status="completed",
            total_points=9,
            completed_points=9,
        )
        region = ScanRegion(x_start=0.0, x_stop=30.0, y_start=0.0, y_stop=30.0, x_step=10.0, y_step=10.0)
        config = ScanPathConfig(scan_mode="snake", dwell_ms=100, speed_mm_min=600.0)
        before = len(self.service.list_tasks())
        record = self.service.register_completed_mock_scan(snapshot, region, config)
        self.assertEqual(len(self.service.list_tasks()), before + 1)
        self.assertEqual(record.point_count, 9)


if __name__ == "__main__":
    unittest.main()
