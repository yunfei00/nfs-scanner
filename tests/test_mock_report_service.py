"""Tests for mock report service."""

from __future__ import annotations

import tempfile
import unittest

from nfs_scanner.core.mock_analysis_service import MockAnalysisService
from nfs_scanner.core.mock_project_service import MockProjectService
from nfs_scanner.core.mock_report_service import MockReportService


class MockReportServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis = MockAnalysisService()
        self.project = MockProjectService()
        self.project.open_mock_project()
        self.service = MockReportService(self.analysis, self.project)

    def test_build_preview(self) -> None:
        task_id = self.analysis.list_tasks()[0].task_id
        preview = self.service.build_preview(task_id)
        self.assertIn("project", preview)
        self.assertIn("scan", preview)
        self.assertEqual(preview["scan"]["task_id"], task_id)

    def test_export_markdown_report(self) -> None:
        task_id = self.analysis.list_tasks()[0].task_id
        with tempfile.TemporaryDirectory() as tmp:
            path = self.service.export_markdown_report(task_id, output_dir=tmp)
            self.assertTrue(path.exists())
            content = path.read_text(encoding="utf-8")
            self.assertIn("近场扫描 Mock 报告", content)
            self.assertIn(task_id, content)

    def test_export_mock_report_formats(self) -> None:
        task_id = self.analysis.list_tasks()[0].task_id
        with tempfile.TemporaryDirectory() as tmp:
            for file_format in ("html", "pdf", "png"):
                path = self.service.export_mock_report(task_id, file_format=file_format, output_dir=tmp)
                self.assertTrue(path.exists())
                self.assertEqual(path.suffix.lower(), f".{file_format}")


if __name__ == "__main__":
    unittest.main()
