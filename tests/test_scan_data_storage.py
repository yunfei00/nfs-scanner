"""Scan data storage tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from nfs_scanner.core.scan_data_storage import RealScanPointRecord, ScanDataStorage


class TestScanDataStorage(unittest.TestCase):
    def test_save_csv_npz_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            storage = ScanDataStorage(project_id="proj", base_dir=Path(tmp) / "run")
            record = RealScanPointRecord(
                index=1,
                x_mm=1.0,
                y_mm=2.0,
                z_mm=3.0,
                timestamp="2026-06-28T12:00:00",
                peak_frequency_hz=2.45e9,
                peak_amplitude_dbm=-30.0,
                frequencies_hz=[2.4e9, 2.5e9],
                amplitudes_dbm=[-40.0, -20.0],
            )
            storage.append_point(record)
            output = storage.finalize({"project_id": "proj", "mode": "test"})
            self.assertTrue((output / "scan_points.csv").is_file())
            self.assertTrue((output / "metadata.json").is_file())
            self.assertTrue((output / "traces.npz").is_file())
            metadata = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["project_id"], "proj")
            with np.load(output / "traces.npz", allow_pickle=True) as npz:
                self.assertEqual(int(npz["index"][0]), 1)


if __name__ == "__main__":
    unittest.main()
