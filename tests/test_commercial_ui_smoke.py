"""Smoke test for commercial UI shell construction."""

from __future__ import annotations

import os
import sys
import unittest

from PySide6.QtWidgets import QApplication

try:
    from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion
    from nfs_scanner.ui.commercial.entry import create_commercial_shell
    from nfs_scanner.ui.commercial.graphics.layers import LayerKind
    from nfs_scanner.ui.commercial.property_panel import CommercialPropertyPanel
    from nfs_scanner.ui.commercial.views.realtime_view import RealtimeView
except ImportError as import_error:  # pragma: no cover - environment dependent
    create_commercial_shell = None  # type: ignore[assignment,misc]
    CommercialPropertyPanel = None  # type: ignore[assignment,misc]
    RealtimeView = None  # type: ignore[assignment,misc]
    ScanRegion = None  # type: ignore[assignment,misc]
    ScanPathConfig = None  # type: ignore[assignment,misc]
    LayerKind = None  # type: ignore[assignment,misc]
    _IMPORT_ERROR = import_error
else:
    _IMPORT_ERROR = None


def _should_skip_gui_test() -> bool:
    """Skip when explicitly requested or no display is available."""

    if os.getenv("NFS_SCANNER_SKIP_GUI_TESTS", "").strip() == "1":
        return True
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True
    return False


@unittest.skipIf(_IMPORT_ERROR is not None, f"Commercial UI dependencies unavailable: {_IMPORT_ERROR}")
@unittest.skipIf(_should_skip_gui_test(), "GUI smoke test skipped in headless environment")
class CommercialUiSmokeTestCase(unittest.TestCase):
    """Verify CommercialMainShell can be imported and constructed."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication(sys.argv)

    def test_create_commercial_shell(self) -> None:
        shell = create_commercial_shell()
        try:
            self.assertEqual(shell.objectName(), "commercialMainShell")
            self.assertTrue(shell.uses_custom_title_bar())
            self.assertIsNotNone(shell.title_bar)
            self.assertIsNotNone(shell.toolbar)
            self.assertIsNotNone(shell.workflow_panel)
            self.assertIsNotNone(shell.device_status_panel)
            self.assertIsNotNone(shell.workspace)
            self.assertIsNotNone(shell.property_panel)
            self.assertIsNotNone(shell.bottom_dock)
        finally:
            shell.close()

    def test_shell_uses_service_bundle(self) -> None:
        from nfs_scanner.ui.commercial.services import create_commercial_services

        services = create_commercial_services()
        shell = create_commercial_shell(services=services)
        try:
            self.assertIs(services.runtime, shell.mock_scan.service)
            self.assertEqual(len(services.devices.list_devices()), 4)
            self.assertIsNotNone(services.motion_connection)
            if shell.toolbar._connect_device_button is not None:
                self.assertTrue(shell.toolbar._connect_device_button.isEnabled())
        finally:
            shell.close()

    def test_property_panel_and_realtime_view_construct(self) -> None:
        panel = CommercialPropertyPanel()
        view = RealtimeView()
        try:
            self.assertTrue(hasattr(panel, "scan_config_changed"))
            self.assertTrue(hasattr(view, "update_path_preview"))
            region = panel.current_scan_region()
            config = panel.current_scan_path_config()
            view.update_path_preview(region, config)
        finally:
            panel.close()
            view.close()

    def test_scan_preview_updates_path_layer(self) -> None:
        shell = create_commercial_shell()
        try:
            view = shell.workspace.realtime_view()
            region = ScanRegion(x_start=0.0, x_stop=50.0, y_start=0.0, y_stop=50.0, x_step=10.0, y_step=10.0)
            config = ScanPathConfig(scan_mode="raster", dwell_ms=100, speed_mm_min=600.0)
            view.update_path_preview(region, config)
            path_layer = view.layer_manager.ensure_layer(LayerKind.PATH)
            self.assertGreater(len(path_layer.items()), 0)
        finally:
            shell.close()

    def test_mock_scan_controller_start_stop(self) -> None:
        from nfs_scanner.ui.commercial.runtime import MockScanController

        controller = MockScanController()
        region = ScanRegion(x_start=0.0, x_stop=20.0, y_start=0.0, y_stop=20.0, x_step=10.0, y_step=10.0)
        config = ScanPathConfig(scan_mode="snake", dwell_ms=50, speed_mm_min=600.0)
        snapshots: list = []
        controller.snapshot_changed.connect(snapshots.append)
        controller.start(region, config)
        self.assertEqual(snapshots[-1].status, "running")
        controller.pause()
        self.assertEqual(snapshots[-1].status, "paused")
        controller.resume()
        self.assertEqual(snapshots[-1].status, "running")
        controller.stop()
        self.assertEqual(snapshots[-1].status, "stopped")

    def test_data_view_lists_mock_tasks(self) -> None:
        from nfs_scanner.ui.commercial.views.data_view import DataView

        view = DataView()
        try:
            self.assertGreaterEqual(view.analysis_service.list_tasks().__len__(), 2)
            view.refresh_tasks()
            self.assertIsNotNone(view._task_list)
            assert view._task_list is not None
            self.assertGreaterEqual(view._task_list.count(), 2)
        finally:
            view.close()

    def test_shell_device_center_syncs_sidebar(self) -> None:
        shell = create_commercial_shell()
        try:
            center = shell.workspace.device_center_view()
            center._connect("spectrum-001")
            sidebar_device = next(
                item
                for item in shell._services.devices.list_devices()
                if item.device_id == "spectrum-001"
            )
            self.assertEqual(sidebar_device.connection_status, "connected")
        finally:
            shell.close()

    def test_mock_scan_emits_dry_run_commands(self) -> None:
        from nfs_scanner.ui.commercial.services import create_commercial_services

        services = create_commercial_services()
        shell = create_commercial_shell(services=services)
        try:
            shell._start_mock_scan()
            self.assertGreaterEqual(len(services.dry_run.log.entries()), 2)
            runtime = shell.mock_scan.service
            if hasattr(runtime, "tick"):
                snapshot = runtime.tick()
                shell._on_mock_scan_snapshot(snapshot)
            self.assertGreaterEqual(len(services.dry_run.log.entries()), 4)
            line = services.dry_run.log.entries()[-1].format_line()
            self.assertIn("DRY RUN", line)
        finally:
            shell.close()

    def test_high_density_preview_samples_path_markers(self) -> None:
        view = RealtimeView()
        try:
            region = ScanRegion(
                x_start=0.0,
                x_stop=100.0,
                y_start=0.0,
                y_stop=100.0,
                x_step=1.0,
                y_step=1.0,
            )
            config = ScanPathConfig(scan_mode="snake", dwell_ms=100, speed_mm_min=600.0)
            view.update_path_preview(region, config)
            path_layer = view.layer_manager.ensure_layer(LayerKind.PATH)
            self.assertGreater(path_layer.point_count, 400)
            self.assertLess(len(path_layer.items()), path_layer.point_count)
        finally:
            view.close()


if __name__ == "__main__":
    unittest.main()
