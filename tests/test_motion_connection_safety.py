"""Safety tests for Sprint 015 motion connection only."""

from __future__ import annotations

import os
import sys
import unittest

from PySide6.QtWidgets import QApplication

from nfs_scanner.core.device_config import MotionDeviceConfig
from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR, is_real_device_control_allowed
from nfs_scanner.core.mock_device_service import MockDeviceService
from nfs_scanner.core.motion_connection_adapter import MotionConnectionAdapter, MotionControlForbiddenError
from nfs_scanner.core.serial_discovery import list_serial_ports
from nfs_scanner.ui.commercial.entry import create_commercial_shell
from nfs_scanner.ui.commercial.services import create_commercial_services
from nfs_scanner.ui.commercial.views.device_center_view import DeviceCenterView


def _should_skip_gui_test() -> bool:
    if os.getenv("NFS_SCANNER_SKIP_GUI_TESTS", "").strip() == "1":
        return True
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True
    return False


class MotionConnectionSafetyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)

    def tearDown(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)

    def test_list_serial_ports_never_raises(self) -> None:
        ports = list_serial_ports()
        self.assertIsInstance(ports, list)

    def test_mock_mode_connect_without_real_env(self) -> None:
        service = MockDeviceService()
        config = create_commercial_services().device_config
        config.set_motion("motion-001", MotionDeviceConfig(connection_mode="mock"))
        view = DeviceCenterView(service, config, MotionConnectionAdapter())
        try:
            view._connect("motion-001")
            device = next(item for item in service.list_devices() if item.device_id == "motion-001")
            self.assertEqual(device.connection_status, "connected")
        finally:
            view.close()

    def test_real_connection_rejected_without_env(self) -> None:
        service = MockDeviceService()
        bundle = create_commercial_services()
        bundle.device_config.set_motion(
            "motion-001",
            MotionDeviceConfig(port="COM3", connection_mode="real_connection_test"),
        )
        view = DeviceCenterView(service, bundle.device_config, bundle.motion_connection)
        try:
            view._connect("motion-001")
            device = next(item for item in service.list_devices() if item.device_id == "motion-001")
            self.assertNotEqual(device.connection_status, "connected")
        finally:
            view.close()

    def test_adapter_blocks_motion_control_methods(self) -> None:
        adapter = MotionConnectionAdapter()
        with self.assertRaises(MotionControlForbiddenError):
            adapter.move_to(1, 2, 3)

    def test_real_device_flag_still_false_by_default(self) -> None:
        self.assertFalse(is_real_device_control_allowed())


@unittest.skipIf(_should_skip_gui_test(), "GUI smoke test skipped in headless environment")
class LegacyUiSmokeTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication(sys.argv)

    def test_commercial_shell_constructs(self) -> None:
        shell = create_commercial_shell()
        try:
            center = shell.workspace.device_center_view()
            self.assertIsNotNone(center)
        finally:
            shell.close()


if __name__ == "__main__":
    unittest.main()
