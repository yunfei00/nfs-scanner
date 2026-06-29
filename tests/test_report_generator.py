"""Tests for HTML report generator."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nfs_scanner.core.report_generator import generate_html_report


class ReportGeneratorTestCase(unittest.TestCase):
    def test_generate_html_report_creates_nonempty_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            import nfs_scanner.core.report_generator as module

            original = module.REPORTS_DIR
            try:
                module.REPORTS_DIR = Path(tmp)
                path = generate_html_report(
                    project_name="Demo Near Field Scan",
                    project_id="demo-project-001",
                    scan_summary={"scan_status": "idle", "point_count": 6461, "region_label": "X 0-180"},
                    device_summary=[{"display_name": "Mock Camera", "connection_status": "connected"}],
                    log_lines=["[SCAN] Dry run scan started"],
                )
                self.assertTrue(path.is_file())
                content = path.read_text(encoding="utf-8")
                self.assertIn("Demo Near Field Scan", content)
                self.assertGreater(len(content), 100)
            finally:
                module.REPORTS_DIR = original


if __name__ == "__main__":
    unittest.main()
