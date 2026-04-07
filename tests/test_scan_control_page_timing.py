"""Scan timing behavior checks for the scan control page."""

from __future__ import annotations

import os
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nfs_scanner.ui.widgets.scan_control_page import ScanControlPage


class ScanControlPageTimingTestCase(unittest.TestCase):
    """验证扫描 ETA 与暂停恢复的时间显示逻辑。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.page = ScanControlPage()
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

    def test_start_scan_displays_remaining_time_and_eta(self) -> None:
        """开始扫描后应立即显示剩余时间和绝对完成时刻。"""

        self.page.on_start_scan()

        self.assertIsNotNone(self.page._remaining_seconds_estimate)
        self.assertIsNotNone(self.page._estimated_completion_time)
        self.assertIn("预计完成:", self.page.time_status_label.text())
        self.assertNotIn("预计完成: --", self.page.time_status_label.text())
        self.assertNotIn("剩余: --", self.page.time_status_label.text())

    def test_pause_freezes_eta_and_resume_reanchors_it(self) -> None:
        """暂停时冻结 ETA，恢复后基于恢复时刻继续累计。"""

        self.page.on_start_scan()
        eta_before_pause = self.page._estimated_completion_time
        remaining_before_pause = self.page._get_display_remaining_seconds()

        time.sleep(0.2)
        self.page.on_pause_scan()
        frozen_eta = self.page._estimated_completion_time
        frozen_remaining = self.page._remaining_seconds_estimate

        self.assertEqual(frozen_eta, eta_before_pause)
        self.assertIsNotNone(frozen_remaining)
        self.assertIsNotNone(remaining_before_pause)
        self.assertLessEqual(frozen_remaining, remaining_before_pause)

        time.sleep(0.2)
        self.assertEqual(self.page._get_display_remaining_seconds(), frozen_remaining)

        self.page._dispatch_next_scan_point = lambda: None
        self.page.on_start_scan()

        self.assertFalse(self.page._scan_paused)
        self.assertIsNotNone(self.page._estimated_completion_time)
        self.assertGreater(self.page._estimated_completion_time, frozen_eta)


if __name__ == "__main__":
    unittest.main()
