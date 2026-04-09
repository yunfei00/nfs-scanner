"""Tests for version traceability across config, plugin, and data layers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nfs_scanner.config.app_config import migrate_config_if_needed
from nfs_scanner.core import DeviceManager
from nfs_scanner.devices.spectrum import SpectrumConnectionError, SpectrumPluginMetadata
from nfs_scanner.storage import DatasetManager


class VersioningSystemTestCase(unittest.TestCase):
    """Verify minimum compatibility guarantees for the new versioning system."""

    def test_config_missing_version_falls_back_to_default(self) -> None:
        """Legacy config payload should be upgraded with default config_version."""

        payload = {"scan": {"start_x": "0"}}
        migrated = migrate_config_if_needed(payload)
        self.assertEqual(migrated["config_version"], "1.0")

    def test_plugin_major_version_mismatch_is_rejected(self) -> None:
        """Plugin API major mismatch should block loading in DeviceManager."""

        with patch(
            "nfs_scanner.core.device_manager.get_spectrum_plugin_metadata",
            return_value=SpectrumPluginMetadata(
                plugin_name="broken-plugin",
                plugin_version="2.3.1",
                plugin_api_version="2.0",
            ),
        ):
            manager = DeviceManager()
            with self.assertRaises(SpectrumConnectionError):
                manager.ensure_spectrum_device(
                    instrument_type="FSW",
                    resource_names=("TCPIP0::192.168.0.10::inst0::INSTR",),
                )

    def test_csv_without_meta_is_backward_compatible(self) -> None:
        """Legacy CSV-only data should still load with fallback metadata."""

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "legacy.csv"
            csv_path.write_text(
                "point_index,x,y,z,freq_100000000Hz\n1,0,0,5,-45\n",
                encoding="utf-8",
            )

            manager = DatasetManager()
            rows, meta = manager.load_scan_points_csv(csv_path)

            self.assertEqual(len(rows), 1)
            self.assertEqual(meta["data_format_version"], "1.0")
            self.assertFalse(meta["meta_file_present"])

    def test_v1_fixture_data_is_recognized(self) -> None:
        """v1.0 sample fixture should parse and expose traceable metadata."""

        fixture_dir = Path("tests/fixtures/data_formats/v1.0")
        csv_path = fixture_dir / "sample_scan.csv"
        manager = DatasetManager()
        rows, meta = manager.load_scan_points_csv(csv_path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(meta["data_format_version"], "1.0")
        self.assertTrue(meta["meta_file_present"])
        self.assertEqual(meta["point_count"], 2)


if __name__ == "__main__":
    unittest.main()
