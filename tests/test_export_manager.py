"""Tests for export manager."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from nfs_scanner.core.export_manager import export_scan_csv, export_scan_json
from nfs_scanner.core.mock_point_data import demo_sample_rows
from nfs_scanner.core.output_paths import EXPORTS_DIR


class ExportManagerTestCase(unittest.TestCase):
    def test_export_scan_csv_creates_nonempty_file(self) -> None:
        rows = demo_sample_rows(count=5)
        with tempfile.TemporaryDirectory() as tmp:
            original = EXPORTS_DIR
            try:
                import nfs_scanner.core.export_manager as module

                module.EXPORTS_DIR = Path(tmp)
                path = export_scan_csv(rows, prefix="scan_data")
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)
                with path.open(encoding="utf-8") as handle:
                    reader = csv.DictReader(handle)
                    parsed = list(reader)
                self.assertEqual(len(parsed), 5)
            finally:
                module.EXPORTS_DIR = original

    def test_export_scan_json_creates_payload(self) -> None:
        rows = demo_sample_rows(count=3)
        with tempfile.TemporaryDirectory() as tmp:
            import nfs_scanner.core.export_manager as module

            original = module.EXPORTS_DIR
            try:
                module.EXPORTS_DIR = Path(tmp)
                path = export_scan_json(rows, prefix="scan_result")
                text = path.read_text(encoding="utf-8")
                self.assertIn("mock_mode", text)
                self.assertIn("rows", text)
            finally:
                module.EXPORTS_DIR = original


if __name__ == "__main__":
    unittest.main()
