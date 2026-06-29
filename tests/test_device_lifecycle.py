"""Commercial V1 device lifecycle acceptance tests."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from nfs_scanner.core.devices.simulation_provider import CORE_DEVICE_IDS, SimulationDeviceProvider
from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR, is_real_device_control_allowed
from nfs_scanner.core.mock_device_config_service import MockDeviceConfigService
from nfs_scanner.core.mock_device_service import MockDeviceService
from nfs_scanner.core.project import NewProjectRequest
from nfs_scanner.ui.commercial.action_handlers import build_action_registry
from nfs_scanner.ui.commercial.entry import create_commercial_shell
from nfs_scanner.ui.commercial.demo_state_sync import devices_ready


def _should_skip_gui_test() -> bool:
    if os.getenv("NFS_SCANNER_SKIP_GUI_TESTS", "").strip() == "1":
        return True
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True
    return False


class SimulationProviderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop(REAL_DEVICE_ENV_VAR, None)
        self.provider = SimulationDeviceProvider(MockDeviceService())

    def test_initial_core_devices_disconnected(self) -> None:
        for device in self.provider.mock_service.list_devices():
            if device.device_id in CORE_DEVICE_IDS:
                self.assertEqual(device.connection_status, "disconnected")

    def test_connect_all_marks_core_devices_connected(self) -> None:
        self.provider.connect_all()
        for device in self.provider.mock_service.list_devices():
            if device.device_id in CORE_DEVICE_IDS:
                self.assertEqual(device.connection_status, "connected")
        self.assertTrue(any("DRY RUN" in line for line in self.provider.command_log))

    def test_disconnect_single_device(self) -> None:
        self.provider.connect_all()
        self.provider.disconnect_device("spectrum-001")
        spectrum = next(
            item for item in self.provider.mock_service.list_devices() if item.device_id == "spectrum-001"
        )
        self.assertEqual(spectrum.connection_status, "disconnected")

    def test_disconnect_all(self) -> None:
        self.provider.connect_all()
        self.provider.disconnect_all()
        for device in self.provider.mock_service.list_devices():
            if device.device_id in CORE_DEVICE_IDS:
                self.assertEqual(device.connection_status, "disconnected")

    def test_refresh_updates_last_message(self) -> None:
        before = next(
            item for item in self.provider.mock_service.list_devices() if item.device_id == "motion-001"
        )
        self.provider.refresh_device("motion-001")
        after = next(
            item for item in self.provider.mock_service.list_devices() if item.device_id == "motion-001"
        )
        self.assertIn("refreshed", after.last_message.lower())
        self.assertNotEqual(before.last_message, after.last_message)

    def test_configure_logs_dry_run(self) -> None:
        result = self.provider.configure("motion-001", {"port": "COM9"})
        self.assertTrue(result.dry_run)
        self.assertTrue(any("CONFIG" in line for line in self.provider.command_log))

    def test_no_real_hardware_flag(self) -> None:
        self.assertFalse(is_real_device_control_allowed())


class DeviceConfigProjectTestCase(unittest.TestCase):
    def test_export_import_roundtrip(self) -> None:
        service = MockDeviceConfigService()
        from nfs_scanner.core.device_config import MotionDeviceConfig

        service.set_motion("motion-001", MotionDeviceConfig(port="COM9", baudrate=9600))
        payload = service.export_project_payload()
        self.assertTrue(payload.get("mock_only"))
        restored = MockDeviceConfigService()
        restored.import_project_payload(payload)
        motion = restored.get_motion("motion-001")
        self.assertEqual(motion.port, "COM9")
        self.assertEqual(motion.baudrate, 9600)


@unittest.skipIf(_should_skip_gui_test(), "GUI device lifecycle tests skipped in headless environment")
class DeviceLifecycleUiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication(sys.argv)

    def test_connect_all_syncs_sidebar_and_device_center(self) -> None:
        shell = create_commercial_shell()
        try:
            shell._on_connect_device()
            self._app.processEvents()
            self.assertTrue(devices_ready(shell._services.devices))
            center = shell.workspace.device_center_view()
            self.assertIn("DRY RUN", center._dry_run_log_view.toPlainText())
        finally:
            shell.close()

    def test_device_config_marks_project_dirty_and_persists(self) -> None:
        shell = create_commercial_shell()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                shell._on_new_project(
                    request=NewProjectRequest(
                        project_name="DeviceLifecycleQA",
                        base_dir=Path(tmp),
                        template="标准扫描",
                    )
                )
                self._app.processEvents()
                from nfs_scanner.core.device_config import MotionDeviceConfig

                shell._services.device_config.set_motion(
                    "motion-001",
                    MotionDeviceConfig(port="COM8"),
                )
                shell._on_device_config_saved("motion COM8")
                self.assertTrue(shell._services.project.is_dirty())
                shell._on_save_project()
                project_file = shell._services.project.project_dir / "project.nfsproj"
                data = json.loads(project_file.read_text(encoding="utf-8"))
                motion_cfg = data.get("device_config", {}).get("motion", {}).get("motion-001", {})
                self.assertEqual(motion_cfg.get("port"), "COM8")
        finally:
            shell.close()

    def test_device_actions_have_handlers(self) -> None:
        shell = create_commercial_shell()
        try:
            registry = build_action_registry(shell)
            for key in (
                "device.connect_all",
                "device.disconnect_all",
                "device.refresh_all",
                "device.open_center",
                "device.configure",
                "device.test_connection",
                "settings.instrument",
                "settings.save_device_config",
            ):
                action = registry.get(key)
                self.assertIsNotNone(action, msg=key)
                self.assertTrue(action.has_handler(), msg=key)
        finally:
            shell.close()


if __name__ == "__main__":
    unittest.main()
