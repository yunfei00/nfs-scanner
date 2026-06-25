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
            self.assertIsNotNone(shell.toolbar)
            self.assertIsNotNone(shell.workflow_panel)
            self.assertIsNotNone(shell.device_status_panel)
            self.assertIsNotNone(shell.workspace)
            self.assertIsNotNone(shell.property_panel)
            self.assertIsNotNone(shell.bottom_dock)
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
