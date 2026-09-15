"""Regression tests for the single supported desktop interface."""

from __future__ import annotations

import os
import sys
import unittest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QScrollArea, QSplitter

from nfs_scanner.application import ApplicationContext
from nfs_scanner.core import DeviceManager, ScanManager
from nfs_scanner.ui.main_window import MainWindow
from nfs_scanner.ui.theme import load_theme
from nfs_scanner.ui.widgets.scan_control_layout import ScanControlLayoutMixin
from nfs_scanner.ui.widgets.scan_control_lifecycle import ScanControlLifecycleMixin
from nfs_scanner.ui.widgets.scan_control_page import ScanControlPage, ScanWorker
from nfs_scanner.ui.widgets.scan_control_support import ScanControlSupportMixin
from nfs_scanner.ui.widgets.instrument_operations import InstrumentOperationsMixin
from nfs_scanner.ui.widgets.scan_workers import ScanWorker as ExtractedScanWorker
from nfs_scanner.version import APP_VERSION


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

    def test_single_shell_contains_scan_workspace(self) -> None:
        self.assertEqual(self.window.objectName(), "mainWindow")
        self.assertIsInstance(self.window.scan_control_page, ScanControlPage)
        self.assertGreaterEqual(self.window.minimumWidth(), 1180)
        self.assertGreaterEqual(self.window.minimumHeight(), 700)

    def test_window_uses_native_title_bar(self) -> None:
        self.assertFalse(self.window.windowFlags() & Qt.WindowType.FramelessWindowHint)
        self.assertIn(f"NFS Scanner v{APP_VERSION}", self.window.windowTitle())

    def test_both_workspace_columns_are_scrollable(self) -> None:
        page = self.window.scan_control_page
        left = page.findChild(QScrollArea, "controlSidebarScroll")
        right = page.findChild(QScrollArea, "measurementWorkspaceScroll")
        self.assertIsNotNone(left)
        self.assertIsNotNone(right)
        self.assertTrue(left.widgetResizable())  # type: ignore[union-attr]
        self.assertTrue(right.widgetResizable())  # type: ignore[union-attr]

    def test_left_controls_fit_scaled_workspace(self) -> None:
        page = self.window.scan_control_page
        page.port_combo.addItem("COM123 - USB Serial Port with a very long company driver description " * 8, "COM123")
        page.port_combo.setCurrentIndex(page.port_combo.count() - 1)
        self.window.resize(1440, 760)
        self.window.show()
        self.app.processEvents()
        splitter = page.findChild(QSplitter, "mainWorkspaceSplitter")
        left = page.findChild(QScrollArea, "controlSidebarScroll")
        self.assertIsNotNone(splitter)
        self.assertIsNotNone(left)
        splitter.setSizes([410, 1000])  # type: ignore[union-attr]
        self.app.processEvents()
        viewport = left.viewport()  # type: ignore[union-attr]
        for control in (page.open_serial_button,page.close_serial_button,page.refresh_ports_button,page.port_combo,*page.jog_step_buttons.values(),page.abs_x_edit,page.abs_y_edit,page.abs_z_edit,page.abs_f_edit,page.scan_speed_edit,page.set_start_point_button,page.set_end_point_button):
            top_left = control.mapTo(viewport, control.rect().topLeft())
            bottom_right = control.mapTo(viewport, control.rect().bottomRight())
            label = control.text() if hasattr(control, "text") else control.objectName()
            self.assertGreaterEqual(top_left.x(), 0, label)
            self.assertLess(bottom_right.x(), viewport.width(), label)

    def test_scan_table_uses_user_facing_chinese_headers(self) -> None:
        page = self.window.scan_control_page
        headers = [page.scan_table.horizontalHeaderItem(index).text() for index in range(page.scan_table.columnCount())]
        self.assertEqual(headers[0], "起点 X"); self.assertEqual(headers[-1], "步距 Z"); self.assertNotIn("start_x", headers); self.assertEqual(page.scan_table.horizontalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def test_instrument_panels_scroll_only_when_needed(self) -> None:
        page = self.window.scan_control_page
        self.assertEqual(page.instrument_tabs.objectName(), "instrumentTabs"); self.assertEqual(page.instrument_section.body_frame.objectName(), "compactSectionBody")
        for panel in page.instrument_panels:
            self.assertEqual(panel.scroll_area.verticalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAsNeeded); self.assertEqual(panel.scroll_area.horizontalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def test_refactored_page_preserves_public_handlers(self) -> None:
        page = self.window.scan_control_page
        self.assertIsInstance(page, ScanControlLayoutMixin); self.assertIsInstance(page, ScanControlLifecycleMixin); self.assertIsInstance(page, ScanControlSupportMixin); self.assertIsInstance(page, InstrumentOperationsMixin); self.assertIs(ScanWorker, ExtractedScanWorker)
        for handler_name in ("on_open_serial", "on_close_serial", "on_start_scan", "on_pause_scan", "on_stop_scan", "on_search_instruments"):
            self.assertTrue(callable(getattr(page, handler_name)))


class UnifiedThemeTestCase(unittest.TestCase):
    def test_theme_uses_native_light_baseline(self) -> None:
        self.assertEqual(load_theme(), "")


if __name__ == "__main__":
    unittest.main()
