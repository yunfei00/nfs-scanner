"""Tests for scan point calculation used by Dry Run UI."""

from __future__ import annotations

import unittest

from nfs_scanner.core.path_planner import calculate_preview_stats, generate_preview_points
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion


class ScanSimulatorTestCase(unittest.TestCase):
    def test_standard_scan_point_count(self) -> None:
        region = ScanRegion(
            x_start=0.0,
            x_stop=180.0,
            y_start=0.0,
            y_stop=140.0,
            z_height=5.0,
            x_step=2.0,
            y_step=2.0,
        )
        path_config = ScanPathConfig()
        points = generate_preview_points(region, path_config)
        stats = calculate_preview_stats(points, region, path_config)
        self.assertEqual(len(points), 6461)
        self.assertEqual(stats.point_count, 6461)

    def test_x_axis_count_is_91(self) -> None:
        region = ScanRegion(x_start=0.0, x_stop=180.0, y_start=0.0, y_stop=0.0, x_step=2.0, y_step=2.0)
        xs = {point[0] for point in generate_preview_points(region, ScanPathConfig())}
        self.assertEqual(len(xs), 91)


if __name__ == "__main__":
    unittest.main()
