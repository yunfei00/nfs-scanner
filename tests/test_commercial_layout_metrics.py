"""Unit tests for commercial layout metric checks."""

from __future__ import annotations

import unittest

from nfs_scanner.ui.commercial.layout_metrics import CommercialLayoutMetrics, _build_checks


class CommercialLayoutMetricsTestCase(unittest.TestCase):
    def test_build_checks_passes_for_valid_default_metrics(self) -> None:
        metrics = CommercialLayoutMetrics(
            uses_custom_title_bar=True,
            title_bar_height=52,
            bottom_dock_height=240,
            log_view_height=120,
            statistics_panel_height=130,
            left_panel_width=240,
            right_panel_width=350,
            workspace_width=720,
            canvas_width=560,
            canvas_height=320,
            canvas_to_right_ratio=1.75,
            canvas_to_left_ratio=2.33,
            canvas_view_area_ratio=0.58,
            colorbar_gap_px=4,
            toolbar_overflow=False,
            status_bar_visible=True,
            window_width=1600,
            window_height=900,
            screen_available_width=1920,
            screen_available_height=1080,
            is_maximized=False,
            workflow_panel_height=320,
            device_status_panel_height=280,
            device_status_collapsed_height=72,
            device_status_has_inner_scroll=False,
            property_tab_bar_visible_after_scroll=True,
            numeric_field_line_edit_min_width=52,
            numeric_field_total_min_width=88,
            action_buttons_count=3,
            action_buttons_overlap=False,
            action_buttons_clipped=False,
            realtime_toolbar_min_button_width=52,
            realtime_toolbar_has_ellipsis=False,
            lut_combo_count=2,
            lut_combos_include_common=True,
        )
        metrics.checks = _build_checks(metrics)
        self.assertTrue(metrics.all_passed())

    def test_build_checks_fails_when_log_too_small(self) -> None:
        metrics = CommercialLayoutMetrics(
            uses_custom_title_bar=True,
            title_bar_height=52,
            bottom_dock_height=240,
            log_view_height=80,
            statistics_panel_height=130,
            canvas_width=560,
            canvas_height=320,
            canvas_to_right_ratio=1.75,
            canvas_to_left_ratio=2.33,
            canvas_view_area_ratio=0.58,
            colorbar_gap_px=4,
            toolbar_overflow=False,
            status_bar_visible=True,
            left_panel_width=240,
            right_panel_width=350,
            workspace_width=720,
            window_width=1600,
            window_height=900,
            screen_available_width=1920,
            screen_available_height=1080,
            is_maximized=False,
            workflow_panel_height=320,
            device_status_panel_height=280,
            device_status_collapsed_height=72,
            device_status_has_inner_scroll=False,
            property_tab_bar_visible_after_scroll=True,
            numeric_field_line_edit_min_width=52,
            numeric_field_total_min_width=88,
            action_buttons_count=3,
            action_buttons_overlap=False,
            action_buttons_clipped=False,
            realtime_toolbar_min_button_width=52,
            realtime_toolbar_has_ellipsis=False,
            lut_combo_count=2,
            lut_combos_include_common=True,
        )
        metrics.checks = _build_checks(metrics)
        self.assertFalse(metrics.all_passed())

    def test_center_canvas_priority_fails_when_canvas_too_narrow(self) -> None:
        metrics = CommercialLayoutMetrics(
            uses_custom_title_bar=True,
            title_bar_height=52,
            bottom_dock_height=240,
            log_view_height=110,
            statistics_panel_height=130,
            left_panel_width=240,
            right_panel_width=350,
            workspace_width=720,
            canvas_width=480,
            canvas_height=320,
            canvas_to_right_ratio=1.5,
            canvas_to_left_ratio=2.0,
            canvas_view_area_ratio=0.52,
            colorbar_gap_px=4,
            toolbar_overflow=False,
            status_bar_visible=True,
            window_width=1280,
            window_height=720,
            screen_available_width=1280,
            screen_available_height=720,
            is_maximized=False,
            workflow_panel_height=320,
            device_status_panel_height=220,
            device_status_collapsed_height=72,
            device_status_has_inner_scroll=False,
            property_tab_bar_visible_after_scroll=True,
            numeric_field_line_edit_min_width=52,
            numeric_field_total_min_width=88,
            action_buttons_count=3,
            action_buttons_overlap=False,
            action_buttons_clipped=False,
            realtime_toolbar_min_button_width=52,
            realtime_toolbar_has_ellipsis=False,
            lut_combo_count=2,
            lut_combos_include_common=True,
        )
        metrics.checks = _build_checks(metrics)
        priority = next(item for item in metrics.checks if item.name == "center_canvas_priority")
        self.assertFalse(priority.passed)


if __name__ == "__main__":
    unittest.main()
