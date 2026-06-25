"""Tests for dry-run command layer."""

from __future__ import annotations

import unittest

from nfs_scanner.core.dry_run_adapters import DryRunCameraAdapter, DryRunMotionAdapter, DryRunSpectrumAdapter
from nfs_scanner.core.dry_run_bundle import create_dry_run_bundle
from nfs_scanner.core.dry_run_log import DRY_RUN_BANNER, DryRunCommandLog
from nfs_scanner.core.integration_safety import is_real_device_control_allowed


class DryRunLayerTestCase(unittest.TestCase):
    def test_motion_adapter_records_without_hardware(self) -> None:
        log = DryRunCommandLog()
        adapter = DryRunMotionAdapter(log=log)
        adapter.move_to(1.0, 2.0, 3.0)
        self.assertEqual(len(log.entries()), 1)
        self.assertIn("move_to", log.entries()[0].format_line())
        self.assertIn(DRY_RUN_BANNER, log.entries()[0].format_line())

    def test_spectrum_adapter_returns_mock_trace(self) -> None:
        bundle = create_dry_run_bundle()
        trace = bundle.spectrum.query_trace(points=5)
        self.assertEqual(len(trace), 5)
        self.assertGreater(max(trace), 0.5)

    def test_camera_adapter_returns_placeholder(self) -> None:
        adapter = DryRunCameraAdapter(log=DryRunCommandLog())
        payload = adapter.capture_frame()
        self.assertEqual(payload["status"], "mock_placeholder")

    def test_dry_run_works_while_real_devices_disabled(self) -> None:
        self.assertFalse(is_real_device_control_allowed())
        bundle = create_dry_run_bundle()
        bundle.motion.home()
        self.assertEqual(len(bundle.log.entries()), 1)


if __name__ == "__main__":
    unittest.main()
