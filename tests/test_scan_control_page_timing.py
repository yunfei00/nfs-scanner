"""UI timing behavior checks for the scan control page."""

from __future__ import annotations

import os
import unittest
from datetime import datetime, timedelta

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nfs_scanner.core import ScanManager
from nfs_scanner.ui.widgets.scan_control_page import ScanControlPage


class FakeClock:
    """Small deterministic clock used by UI timing tests."""

    def __init__(self) -> None:
        self._now = datetime(2026, 4, 7, 14, 30, 0)
        self._monotonic = 0.0

    def now(self) -> datetime:
        return self._now

    def monotonic(self) -> float:
        return self._monotonic

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)
        self._monotonic += seconds


class ScanControlPageTimingTestCase(unittest.TestCase):
    """Verify that the page reflects scan timing from the manager layer."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.clock = FakeClock()
        self.scan_manager = ScanManager(
            now_provider=self.clock.now,
            monotonic_provider=self.clock.monotonic,
        )
        self.page = ScanControlPage(scan_manager=self.scan_manager)
        self.page.clock_timer.stop()
        self.page._scan_timer.stop()
        self.page.serial_is_open = True
        self.page.SCAN_DISPATCH_INTERVAL_MS = 5000
        self.page._build_scan_points = lambda: [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
        self.page._prepare_scan_storage_workspace = lambda: None
        self.page._save_scan_plan_snapshot = lambda: None
        self.page._save_scan_execution_snapshot = lambda completed: None
        self.page._capture_and_store_scan_point = lambda **kwargs: (True, "ok")
        self.page._send_serial_command = lambda command: (True, "ok")

    def tearDown(self) -> None:
        self.page.close()

    def test_page_reads_eta_from_scan_manager(self) -> None:
        """Starting a scan should display manager-provided remaining time and ETA."""

        self.page.on_start_scan()

        snapshot = self.scan_manager.get_scan_runtime_snapshot()
        self.assertEqual(snapshot.status, "running")
        self.assertIsNotNone(snapshot.remaining_seconds)
        self.assertIsNotNone(snapshot.estimated_completion_time)
        self.assertIn(f"剩余: {snapshot.remaining_seconds} 秒", self.page.time_status_label.text())
        self.assertIn(
            f"预计完成: {snapshot.estimated_completion_time.strftime('%H:%M:%S')}",
            self.page.time_status_label.text(),
        )

    def test_pause_freezes_eta_and_resume_reanchors_display(self) -> None:
        """Pause should freeze manager timing, and resume should re-anchor the ETA."""

        self.page.on_start_scan()
        self.clock.advance(2.0)
        self.page._refresh_clock()

        before_pause = self.scan_manager.get_scan_runtime_snapshot()
        self.page.on_pause_scan()
        paused_snapshot = self.scan_manager.get_scan_runtime_snapshot()

        self.assertEqual(paused_snapshot.status, "paused")
        self.assertEqual(paused_snapshot.remaining_seconds, before_pause.remaining_seconds)
        frozen_eta = paused_snapshot.estimated_completion_time
        frozen_remaining = paused_snapshot.remaining_seconds

        self.clock.advance(10.0)
        self.page._refresh_clock()
        self.assertEqual(self.scan_manager.get_scan_runtime_snapshot().remaining_seconds, frozen_remaining)
        self.assertIn(f"剩余: {frozen_remaining} 秒", self.page.time_status_label.text())

        self.page._dispatch_next_scan_point = lambda: None
        self.page.on_start_scan()
        resumed_snapshot = self.scan_manager.get_scan_runtime_snapshot()

        self.assertEqual(resumed_snapshot.status, "running")
        self.assertEqual(resumed_snapshot.remaining_seconds, frozen_remaining)
        self.assertGreater(resumed_snapshot.estimated_completion_time, frozen_eta)

    def test_page_no_longer_tracks_scan_timing_locally(self) -> None:
        """Core timing fields should live in the manager rather than on the page."""

        self.assertFalse(hasattr(self.page, "_scan_started_monotonic"))
        self.assertFalse(hasattr(self.page, "_scan_elapsed_seconds"))
        self.assertFalse(hasattr(self.page, "_remaining_seconds_estimate"))
        self.assertFalse(hasattr(self.page, "_estimated_completion_time"))
        self.assertFalse(hasattr(self.page, "_scan_paused"))


if __name__ == "__main__":
    unittest.main()
