"""Tests for device center view."""

from __future__ import annotations

import os
import sys
import unittest

from PySide6.QtWidgets import QApplication

from nfs_scanner.core.mock_device_service import MockDeviceService
from nfs_scanner.ui.commercial.views.device_center_view import DeviceCenterView


def _should_skip_gui_test() -> bool:
    if os.getenv("NFS_SCANNER_SKIP_GUI_TESTS", "").strip() == "1":
        return True
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True
    return False


@unittest.skipIf(_should_skip_gui_test(), "GUI test skipped in headless environment")
class DeviceCenterViewTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication(sys.argv)

    def test_connect_updates_service_and_emits_signal(self) -> None:
        service = MockDeviceService()
        view = DeviceCenterView(service)
        changes: list[int] = []
        view.devices_changed.connect(lambda: changes.append(1))
        try:
            view._connect("spectrum-001")
            device = next(item for item in service.list_devices() if item.device_id == "spectrum-001")
            self.assertEqual(device.connection_status, "connected")
            self.assertEqual(len(changes), 1)
        finally:
            view.close()


if __name__ == "__main__":
    unittest.main()
