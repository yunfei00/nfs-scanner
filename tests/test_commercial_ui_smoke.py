"""Smoke test for commercial UI shell construction."""

from __future__ import annotations

import os
import sys
import unittest

from PySide6.QtWidgets import QApplication

try:
    from nfs_scanner.ui.commercial.entry import create_commercial_shell
except ImportError as import_error:  # pragma: no cover - environment dependent
    create_commercial_shell = None  # type: ignore[assignment,misc]
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


if __name__ == "__main__":
    unittest.main()
