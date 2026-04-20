"""Tests for FSW CSV storage helpers."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from nfs_scanner.devices.spectrum.fsw_storage import append_fsw_trace_csv, save_fsw_trace_csv


class FswStorageTestCase(unittest.TestCase):
    """Validate FSW single-trace CSV save and append behavior."""

    def test_save_fsw_trace_csv_writes_two_line_layout(self) -> None:
        """Saved file should use `fre` header + one `x_y_z` data row."""

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "fsw.csv"
            point_count = save_fsw_trace_csv(
                frequencies=[1.0, 2.0, 3.0],
                values=[-10.0, -11.5, -12.25],
                x=1.0,
                y=2.0,
                z=3.0,
                file_path=target,
            )

            self.assertEqual(point_count, 3)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "fre,1,2,3\n1_2_3,-10,-11.5,-12.25\n",
            )

    def test_append_fsw_trace_csv_writes_header_once(self) -> None:
        """Combined CSV should only have one frequency header."""

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "all_points.csv"
            append_fsw_trace_csv(
                frequencies=[10.0, 20.0],
                values=[-30.0, -31.0],
                x=0.0,
                y=0.0,
                z=5.0,
                file_path=target,
            )
            append_fsw_trace_csv(
                frequencies=[10.0, 20.0],
                values=[-32.0, -33.0],
                x=1.0,
                y=0.0,
                z=5.0,
                file_path=target,
            )

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "fre,10,20\n0_0_5,-30,-31\n1_0_5,-32,-33\n",
            )

    def test_save_fsw_trace_csv_rejects_mismatched_lengths(self) -> None:
        """Frequency/value length mismatch should raise ValueError."""

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "invalid.csv"
            with self.assertRaisesRegex(ValueError, "频点数量不一致"):
                save_fsw_trace_csv(
                    frequencies=[1.0, 2.0],
                    values=[-10.0],
                    x=0.0,
                    y=0.0,
                    z=0.0,
                    file_path=target,
                )


if __name__ == "__main__":
    unittest.main()
