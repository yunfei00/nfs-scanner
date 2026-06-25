"""Unit tests for commercial layout metric checks."""

from __future__ import annotations

import unittest

from nfs_scanner.ui.commercial.layout_metrics import CommercialLayoutMetrics, _build_checks


class CommercialLayoutMetricsTestCase(unittest.TestCase):
    def test_build_checks_passes_for_valid_default_metrics(self) -> None:
        metrics = CommercialLayoutMetrics(
            uses_custom_title_bar=True,
            title_bar_height=34,
            bottom_dock_height=220,
            log_view_height=140,
            statistics_panel_height=130,
            left_panel_width=280,
            right_panel_width=380,
            workspace_width=720,
            window_width=1600,
            window_height=900,
            screen_available_width=1920,
            screen_available_height=1080,
            is_maximized=False,
        )
        metrics.checks = _build_checks(metrics)
        self.assertTrue(metrics.all_passed())

    def test_build_checks_fails_when_log_too_small(self) -> None:
        metrics = CommercialLayoutMetrics(
            uses_custom_title_bar=True,
            title_bar_height=34,
            bottom_dock_height=220,
            log_view_height=80,
            statistics_panel_height=130,
            left_panel_width=280,
            right_panel_width=380,
            workspace_width=720,
            window_width=1600,
            window_height=900,
            screen_available_width=1920,
            screen_available_height=1080,
            is_maximized=False,
        )
        metrics.checks = _build_checks(metrics)
        self.assertFalse(metrics.all_passed())


if __name__ == "__main__":
    unittest.main()
