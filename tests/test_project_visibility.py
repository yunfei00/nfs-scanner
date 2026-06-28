"""Tests for Commercial V1 project visibility across the shell."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

from nfs_scanner.core.project import NewProjectRequest


@unittest.skipIf(os.getenv("NFS_SCANNER_SKIP_GUI_TESTS") == "1", "GUI tests skipped")
class ProjectVisibilityTestCase(unittest.TestCase):
    def test_project_visible_after_new_project(self) -> None:
        from PySide6.QtWidgets import QApplication

        from nfs_scanner.ui.commercial.entry import create_commercial_shell

        app = QApplication.instance() or QApplication(sys.argv)
        shell = create_commercial_shell()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                name = "VisibilityTestProject"
                shell._on_new_project(
                    request=NewProjectRequest(
                        project_name=name,
                        base_dir=Path(tmp),
                        template="标准扫描",
                    )
                )
                app.processEvents()

                self.assertIn(name, shell.top_header.brand_area.active_project_line())
                self.assertIn(name, shell.status_bar_widget.project_label.text())
                self.assertIn(name, shell.workflow_panel.workflow_project_name())
                self.assertIn(name, shell.project_summary_card.summary_project_name())
                self.assertIn(name, shell.windowTitle())
                self.assertIn(name, shell.workspace.data_view()._project_banner.text())
                self.assertIn(name, shell.workspace.report_view()._project_banner.text())
                self.assertIn("已保存", shell.status_bar_widget.storage_label.text())

                shell.property_panel._field_map["x_step"].setText("4.0")
                shell.property_panel.emit_current_scan_config()
                app.processEvents()
                self.assertIn("*", shell.windowTitle())
                self.assertIn("未保存", shell.status_bar_widget.storage_label.text())

                shell._on_save_project()
                app.processEvents()
                self.assertNotIn("*", shell.windowTitle())
                self.assertIn("已保存", shell.status_bar_widget.storage_label.text())
        finally:
            shell.close()
            app.processEvents()


if __name__ == "__main__":
    unittest.main()
