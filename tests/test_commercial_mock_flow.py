"""Commercial v0.2 mock workflow checks."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication, QComboBox

from nfs_scanner.core.mock_scan_runtime import MockScanRuntimeService
from nfs_scanner.ui.commercial.entry import create_commercial_shell
from nfs_scanner.ui.commercial.lut_presets import COMMON_LUT_NAMES
from nfs_scanner.ui.commercial.widgets import NFSNumericField


def _should_skip_gui_test() -> bool:
    if os.getenv("NFS_SCANNER_SKIP_GUI_TESTS", "").strip() == "1":
        return True
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True
    return False


@unittest.skipIf(_should_skip_gui_test(), "GUI mock flow test skipped in headless environment")
class CommercialMockFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication(sys.argv)

    def test_mock_flow_v0_2(self) -> None:
        shell = create_commercial_shell()
        try:
            shell.show()
            self._app.processEvents()

            self.assertGreaterEqual(shell.toolbar.tool_button_count(), 13)
            self.assertEqual(len(shell._services.devices.list_devices()), 4)

            shell._on_connect_device()
            self._app.processEvents()
            core_ids = {"motion-001", "spectrum-001", "camera-001"}
            connected = {
                item.device_id
                for item in shell._services.devices.list_devices()
                if item.connection_status == "connected"
            }
            self.assertEqual(core_ids, connected)

            center = shell.workspace.device_center_view()
            self.assertIn("NO HARDWARE CONTROL", center._safety_label.text())

            lut_items = {
                combo.itemText(index)
                for combo in shell.findChildren(QComboBox)
                for index in range(combo.count())
            }
            self.assertTrue(set(COMMON_LUT_NAMES).issubset(lut_items))

            numeric_fields = shell.property_panel.findChildren(NFSNumericField)
            self.assertTrue(any(field.line_edit().minimumWidth() >= 72 for field in numeric_fields))

            runtime = shell._services.runtime
            self.assertIsInstance(runtime, MockScanRuntimeService)
            before_tasks = len(shell.workspace.data_view().analysis_service.list_tasks())
            shell._start_mock_scan()
            self._app.processEvents()
            self.assertEqual(shell.mock_scan.snapshot().status, "running")
            shell._toggle_mock_scan_pause()
            self.assertEqual(shell.mock_scan.snapshot().status, "paused")
            shell._toggle_mock_scan_pause()
            self.assertEqual(shell.mock_scan.snapshot().status, "running")
            shell._stop_mock_scan()
            self.assertEqual(shell.mock_scan.snapshot().status, "stopped")

            shell._start_mock_scan()
            status = shell.mock_scan.snapshot().status
            ticks = 0
            while status == "running" and ticks < 10000:
                snapshot = runtime.tick()
                shell._on_mock_scan_snapshot(snapshot)
                self._app.processEvents()
                status = snapshot.status
                ticks += 1
            self.assertEqual(status, "completed")
            self.assertGreater(len(shell.workspace.data_view().analysis_service.list_tasks()), before_tasks)

            data_path = shell.workspace.data_view().export_selected_task()
            self.assertIsNotNone(data_path)
            assert data_path is not None
            self.assertTrue(data_path.exists())

            report_view = shell.workspace.report_view()
            report_view.refresh_tasks()
            report_view._generate_report()
            report_view._export_report("html")
            export_path = report_view.last_export_path()
            self.assertIsNotNone(export_path)

            shell._run_mock_self_check()
            self.assertTrue((Path(".ai") / "qa" / "latest" / "commercial_mock_self_check.json").is_file())
        finally:
            shell.close()


if __name__ == "__main__":
    unittest.main()
