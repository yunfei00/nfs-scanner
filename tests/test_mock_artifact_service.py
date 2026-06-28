"""Tests for mock artifact and point data helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nfs_scanner.core.mock_analysis_service import MockScanTaskRecord
from nfs_scanner.core.mock_artifact_service import MockArtifactService
from nfs_scanner.core.mock_point_data import (
    demo_sample_rows,
    export_table_csv,
    generate_point_rows,
)


class MockArtifactServiceTestCase(unittest.TestCase):
    def test_build_filename_contains_type(self) -> None:
        name = MockArtifactService.build_filename(
            artifact_type="mock_data",
            task_id="t1",
            extension="json",
        )
        self.assertIn("mock_data", name)
        self.assertTrue(name.endswith(".json"))

    def test_export_json_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def _category_dir(cls, category: str) -> Path:
                path = root / category
                path.mkdir(parents=True, exist_ok=True)
                return path

            with patch.object(MockArtifactService, "ROOT", root):
                with patch.object(MockArtifactService, "category_dir", classmethod(_category_dir)):
                    path = MockArtifactService.export_json("data", "test.json", {"ok": True})
            self.assertTrue(path.is_file())
            self.assertIn('"ok": true', path.read_text(encoding="utf-8"))


class MockPointDataTestCase(unittest.TestCase):
    def test_generate_point_rows_count(self) -> None:
        task = MockScanTaskRecord(
            task_id="demo-1",
            name="Demo",
            point_count=25,
            completed_at="2026-06-26 12:00:00",
            scan_mode="snake",
            peak_frequency="2.45 GHz",
            peak_amplitude="-20 dBm",
            area_mm2=100.0,
        )
        rows = generate_point_rows(task, max_rows=200)
        self.assertEqual(len(rows), 25)

    def test_export_table_csv(self) -> None:
        rows = demo_sample_rows(count=5)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def _category_dir(cls, category: str) -> Path:
                path = root / category
                path.mkdir(parents=True, exist_ok=True)
                return path

            with patch.object(MockArtifactService, "ROOT", root):
                with patch.object(MockArtifactService, "category_dir", classmethod(_category_dir)):
                    path = export_table_csv(rows, "demo")
            self.assertTrue(path.is_file())
            self.assertIn("index", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
