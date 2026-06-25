"""Tests for ScanPathLayer display density policy."""

from __future__ import annotations

import unittest

from nfs_scanner.ui.commercial.graphics.path_display_policy import (
    PathDisplayLevel,
    is_high_density_preview,
    resolve_display_level,
    select_arrow_segment_indices,
    select_dot_indices,
)


class PathDisplayPolicyTestCase(unittest.TestCase):
    def test_full_detail_for_small_paths(self) -> None:
        level = resolve_display_level(40)
        self.assertEqual(level, PathDisplayLevel.FULL)
        self.assertEqual(len(select_dot_indices(40, level)), 40)

    def test_reduced_detail_samples_dots(self) -> None:
        level = resolve_display_level(200)
        self.assertEqual(level, PathDisplayLevel.REDUCED)
        dots = select_dot_indices(200, level)
        self.assertLess(len(dots), 200)
        self.assertIn(0, dots)
        self.assertIn(199, dots)

    def test_minimal_detail_for_high_density(self) -> None:
        level = resolve_display_level(800)
        self.assertEqual(level, PathDisplayLevel.MINIMAL)
        dots = select_dot_indices(800, level)
        arrows = select_arrow_segment_indices(800, level)
        self.assertLess(len(dots), 20)
        self.assertLess(len(arrows), 10)
        self.assertTrue(is_high_density_preview(800))

    def test_path_line_keeps_endpoints_in_minimal_mode(self) -> None:
        level = PathDisplayLevel.MINIMAL
        dots = select_dot_indices(500, level)
        self.assertEqual(dots[0], 0)
        self.assertEqual(dots[-1], 499)


if __name__ == "__main__":
    unittest.main()
