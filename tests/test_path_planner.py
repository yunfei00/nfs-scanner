"""Unit tests for scan path preview planner."""

from __future__ import annotations

import unittest

from nfs_scanner.core.path_planner import (
    calculate_preview_stats,
    generate_preview_points,
    generate_raster_points,
    generate_snake_points,
)
from nfs_scanner.core.scan_config import ScanPathConfig, ScanRegion


class PathPlannerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.region = ScanRegion(
            x_start=0.0,
            x_stop=10.0,
            y_start=0.0,
            y_stop=10.0,
            z_height=5.0,
            x_step=5.0,
            y_step=5.0,
        )
        self.config = ScanPathConfig(scan_mode="snake", dwell_ms=100, speed_mm_min=600.0)

    def test_raster_generates_row_major_points(self) -> None:
        points = generate_raster_points(self.region, self.config)
        self.assertEqual(len(points), 9)
        self.assertEqual(points[0], (0.0, 0.0, 5.0))
        self.assertEqual(points[1], (5.0, 0.0, 5.0))
        self.assertEqual(points[3], (0.0, 5.0, 5.0))

    def test_snake_reverses_alternate_rows(self) -> None:
        points = generate_snake_points(self.region, self.config)
        self.assertEqual(len(points), 9)
        self.assertEqual(points[2], (10.0, 0.0, 5.0))
        self.assertEqual(points[3], (10.0, 5.0, 5.0))
        self.assertEqual(points[4], (5.0, 5.0, 5.0))

    def test_preview_stats_include_area_and_time(self) -> None:
        points = generate_preview_points(self.region, self.config)
        stats = calculate_preview_stats(points, self.region, self.config)
        self.assertEqual(stats.point_count, 9)
        self.assertAlmostEqual(stats.area_mm2, 100.0)
        self.assertGreater(stats.path_length_mm, 0.0)
        self.assertGreater(stats.estimated_seconds, 0.0)
        self.assertEqual(stats.scan_mode, "snake")

    def test_raster_mode_via_preview_entry(self) -> None:
        config = ScanPathConfig(scan_mode="raster", dwell_ms=50, speed_mm_min=1200.0)
        points = generate_preview_points(self.region, config)
        stats = calculate_preview_stats(points, self.region, config)
        self.assertEqual(points[3], (0.0, 5.0, 5.0))
        self.assertEqual(stats.scan_mode, "raster")

    def test_high_density_stats_flag(self) -> None:
        dense_region = ScanRegion(
            x_start=0.0,
            x_stop=100.0,
            y_start=0.0,
            y_stop=100.0,
            x_step=1.0,
            y_step=1.0,
        )
        points = generate_preview_points(dense_region, self.config)
        stats = calculate_preview_stats(points, dense_region, self.config)
        self.assertGreater(stats.point_count, 400)
        self.assertTrue(stats.is_high_density)

    def test_invalid_region_is_clamped(self) -> None:
        invalid = ScanRegion(x_start=20.0, x_stop=0.0, y_start=30.0, y_stop=0.0, x_step=0.0, y_step=0.0)
        points = generate_snake_points(invalid, self.config)
        self.assertGreater(len(points), 0)


if __name__ == "__main__":
    unittest.main()
