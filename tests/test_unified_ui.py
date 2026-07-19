"""Regression tests for the single supported desktop interface."""

from __future__ import annotations

import os
import sys
import unittest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QScrollArea, QSizeGrip, QToolButton

from nfs_scanner.application import ApplicationContext
from nfs_scanner.core import DeviceManager, ScanManager
from nfs_scanner.ui.main_window import MainWindow
from nfs_scanner.ui.theme import load_theme
from nfs_scanner.ui.widgets.scan_control_layout import ScanControlLayoutMixin
from nfs_scanner.ui.widgets.scan_control_page import ScanControlPage, ScanWorker
from nfs_scanner.ui.widgets.scan_control_support import ScanControlSupportMixin
from nfs_scanner.ui.widgets.instrument_operations import InstrumentOperationsMixin
from nfs_scanner.ui.widgets.scan_workers import ScanWorker as ExtractedScanWorker


def _skip_gui() -> bool:
    return os.getenv("NFS_SCANNER_SKIP_GUI_TESTS", "").strip() == "1" or (
        sys.platform.startswith("linux") and not os.environ.get("DISPLAY")
    )


@unittest.skipIf(_skip_gui(), "GUI tests skipped")
class UnifiedUiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self._previous_startup_setting = os.environ.get("NFS_SCANNER_DISABLE_AUTO_STARTUP_TASKS")
        os.environ["NFS_SCANNER_DISABLE_AUTO_STARTUP_TASKS"] = "1"
        self.context = ApplicationContext(DeviceManager(), ScanManager())
        self.window = MainWindow(context=self.context)

    def tearDown(self) -> None:
        page = self.window.scan_control_page
        page.clock_timer.stop()
        page._serial_reconnect_timer.stop()
        self.window.close()
        if self._previous_startup_setting is None:
            os.environ.pop("NFS_SCANNER_DISABLE_AUTO_STARTUP_TASKS", None)
        else:
            os.environ["NFS_SCANNER_DISABLE_AUTO_STARTUP_TASKS"] = self._previous_startup_setting

    def test_main_window_uses_injected_proven_interfaces(self) -> None:
        self.assertIs(self.window.device_manager, self.context.device_manager)
        self.assertIs(self.window.scan_manager, self.context.scan_manager)
        self.assertIs(self.window.scan_control_page.device_manager, self.context.device_manager)
        self.assertIs(self.window.scan_control_page.scan_manager, self.context.scan_manager)

    def test_single_shell_contains_header_and_scan_workspace(self) -> None:
        self.assertEqual(self.window.objectName(), "mainWindow")
        self.assertEqual(self.window.header.objectName(), "applicationHeader")
        self.assertIsInstance(self.window.scan_control_page, ScanControlPage)
        self.assertGreaterEqual(self.window.minimumWidth(), 1180)
        self.assertGreaterEqual(self.window.minimumHeight(), 700)

    def test_window_uses_custom_frameless_title_bar(self) -> None:
        self.assertTrue(self.window.windowFlags() & Qt.WindowType.FramelessWindowHint)
        self.assertIsInstance(self.window.size_grip, QSizeGrip)
        for object_name in ("minimizeWindowButton", "maximizeWindowButton", "closeWindowButton"):
            self.assertIsNotNone(self.window.header.findChild(QToolButton, object_name))

    def test_maximized_window_uses_one_clear_restore_symbol(self) -> None:
        self.window.header.sync_window_state(True)

        self.assertEqual(self.window.header.maximize_button.text(), "↙")
        self.assertEqual(self.window.header.maximize_button.accessibleName(), "还原")
        self.assertEqual(len(self.window.header.maximize_button.text()), 1)

        self.window.header.sync_window_state(False)
        self.assertEqual(self.window.header.maximize_button.text(), "□")
        self.assertEqual(self.window.header.maximize_button.accessibleName(), "最大化")

    def test_first_maximize_request_updates_control_without_state_lag(self) -> None:
        header = self.window.header
        self.assertFalse(header.is_maximized)

        header._toggle_maximize()
        header._finish_window_state_request(True)

        self.assertTrue(header.is_maximized)
        self.assertEqual(header.maximize_button.accessibleName(), "还原")

        header._toggle_maximize()
        header._finish_window_state_request(False)
        self.assertFalse(header.is_maximized)
        self.assertEqual(header.maximize_button.accessibleName(), "最大化")

    def test_both_workspace_columns_are_scrollable(self) -> None:
        page = self.window.scan_control_page
        left = page.findChild(QScrollArea, "controlSidebarScroll")
        right = page.findChild(QScrollArea, "measurementWorkspaceScroll")

        self.assertIsNotNone(left)
        self.assertIsNotNone(right)
        self.assertTrue(left.widgetResizable())  # type: ignore[union-attr]
        self.assertTrue(right.widgetResizable())  # type: ignore[union-attr]

    def test_scan_table_uses_user_facing_chinese_headers(self) -> None:
        page = self.window.scan_control_page
        headers = [page.scan_table.horizontalHeaderItem(index).text() for index in range(page.scan_table.columnCount())]

        self.assertEqual(headers[0], "起点 X")
        self.assertEqual(headers[-1], "步距 Z")
        self.assertNotIn("start_x", headers)

    def test_refactored_page_preserves_public_handlers(self) -> None:
        page = self.window.scan_control_page

        self.assertIsInstance(page, ScanControlLayoutMixin)
        self.assertIsInstance(page, ScanControlSupportMixin)
        self.assertIsInstance(page, InstrumentOperationsMixin)
        self.assertIs(ScanWorker, ExtractedScanWorker)
        for handler_name in (
            "on_open_serial",
            "on_close_serial",
            "on_start_scan",
            "on_pause_scan",
            "on_stop_scan",
            "on_search_instruments",
        ):
            self.assertTrue(callable(getattr(page, handler_name)))


class UnifiedThemeTestCase(unittest.TestCase):
    def test_theme_contains_core_engineering_selectors(self) -> None:
        stylesheet = load_theme()

        self.assertIn("QFrame#applicationHeader", stylesheet)
        self.assertIn("QToolButton#closeWindowButton", stylesheet)
        self.assertIn("QPushButton#primaryButton", stylesheet)
        self.assertIn("QPushButton#dangerButton", stylesheet)
        self.assertIn("QScrollArea", stylesheet)


if __name__ == "__main__":
    unittest.main()
