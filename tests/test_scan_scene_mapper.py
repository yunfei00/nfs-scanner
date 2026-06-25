"""Unit tests for scan scene coordinate mapping."""

from __future__ import annotations

import unittest

from nfs_scanner.core.scan_config import ScanRegion
from nfs_scanner.ui.commercial.scan_scene_mapper import map_point_to_scene, map_points_to_scene


class ScanSceneMapperTestCase(unittest.TestCase):
    def test_corners_map_to_board_area(self) -> None:
        region = ScanRegion(x_start=0.0, x_stop=100.0, y_start=0.0, y_stop=100.0)
        top_left = map_point_to_scene(0.0, 0.0, region)
        bottom_right = map_point_to_scene(100.0, 100.0, region)
        self.assertLess(top_left[0], bottom_right[0])
        self.assertLess(top_left[1], bottom_right[1])

    def test_map_points_preserves_count(self) -> None:
        region = ScanRegion(x_start=0.0, x_stop=10.0, y_start=0.0, y_stop=10.0)
        points = [(0.0, 0.0, 5.0), (10.0, 10.0, 5.0)]
        mapped = map_points_to_scene(points, region)
        self.assertEqual(len(mapped), 2)


if __name__ == "__main__":
    unittest.main()
