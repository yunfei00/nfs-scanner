"""Target-page alignment checks for commercial UI final verification."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QFrame, QLabel, QProgressBar, QTabWidget, QWidget

from nfs_scanner.ui.commercial.graphics.layers import LayerKind
from nfs_scanner.ui.commercial.layout_metrics import LayoutMetricCheck
from nfs_scanner.ui.commercial.main_shell import CommercialMainShell
from nfs_scanner.ui.commercial.widgets.mock_chart_widgets import MockSpectrumWidget


def collect_target_alignment_checks(shell: CommercialMainShell) -> list[LayoutMetricCheck]:
    """Build target-screenshot alignment assertions for visual QA."""

    logo = shell.findChild(QFrame, "commercialTitleBarLogo")
    timeline_steps = shell.findChildren(QFrame, "nfsWorkflowTimelineStep")
    tri_panel = shell.findChild(QWidget, "commercialBottomDockTriPanel")
    spectrum = shell.findChild(QWidget, "commercialDockSpectrumPanel")
    stats = shell.findChild(QWidget, "commercialDockStatsPanel")
    log_panel = shell.findChild(QWidget, "commercialDockLogPanel")
    log_view = shell.bottom_dock.log_view_widget()
    realtime = shell.workspace.realtime_view()
    roi_items = realtime.layer_manager.ensure_layer(LayerKind.ANNOTATION).items()
    toolbar_count = shell.toolbar.tool_button_count()
    property_tabs = shell.property_panel.findChild(QTabWidget, "commercialPropertyTabs")
    grid_rows = shell.property_panel.findChildren(QWidget, "commercialPropertyGridRow")
    spectrum_widget = shell.findChild(MockSpectrumWidget, "mockSpectrumWidget")
    log_tags = shell.bottom_dock.has_log_category_tags()

    log_lines = 0
    if log_view is not None:
        log_lines = len(log_view.toPlainText().splitlines())

    target_style = shell.property("targetStyleMode") == "true"
    top_header = shell.findChild(QFrame, "commercialTopHeader")
    brand_row = shell.findChild(QWidget, "commercialBrandRow")
    toolbar_parent = shell.toolbar.parent()
    if hasattr(shell, "top_header"):
        QApplication.processEvents()
        single_line_brand = shell.top_header.is_single_line_brand()
    checks = [
        LayoutMetricCheck(
            name="top_header_integrated",
            expected="toolbar embedded in unified top header",
            actual=f"header={top_header is not None}, parent={getattr(toolbar_parent, 'objectName', lambda: '')()}",
            passed=top_header is not None and toolbar_parent is top_header,
        ),
        LayoutMetricCheck(
            name="brand_single_line_row",
            expected="brand title/subtitle/version on one horizontal row",
            actual=f"row={brand_row is not None}, single_line={single_line_brand}",
            passed=brand_row is not None and single_line_brand,
        ),
        LayoutMetricCheck(
            name="target_style_mode",
            expected="targetStyleMode enabled",
            actual=str(shell.property("targetStyleMode")),
            passed=target_style,
        ),
        LayoutMetricCheck(
            name="logo_area_exists",
            expected="NFS logo block visible",
            actual=f"visible={logo.isVisible() if logo else False}",
            passed=logo is not None and logo.isVisible(),
        ),
        LayoutMetricCheck(
            name="top_toolbar_icon_mode",
            expected=">= 12 toolbar actions",
            actual=str(toolbar_count),
            passed=toolbar_count >= 12,
        ),
        LayoutMetricCheck(
            name="workflow_timeline_mode",
            expected=">= 7 timeline steps",
            actual=str(len(timeline_steps)),
            passed=len(timeline_steps) >= 7,
        ),
        LayoutMetricCheck(
            name="right_compact_grid_form",
            expected="property tabs + xyz grid rows",
            actual=f"tabs={property_tabs is not None}, rows={len(grid_rows)}",
            passed=property_tabs is not None and len(grid_rows) >= 3,
        ),
        LayoutMetricCheck(
            name="bottom_dock_three_panel_mode",
            expected="tri-panel dock visible",
            actual=f"visible={tri_panel.isVisible() if tri_panel else False}",
            passed=tri_panel is not None and tri_panel.isVisible(),
        ),
        LayoutMetricCheck(
            name="spectrum_panel_visible",
            expected="spectrum panel visible",
            actual=f"visible={spectrum.isVisible() if spectrum else False}",
            passed=spectrum is not None and spectrum.isVisible(),
        ),
        LayoutMetricCheck(
            name="spectrum_yellow_curve_mode",
            expected="yellow curve spectrum widget",
            actual=str(spectrum_widget.property("yellowCurveMode") if spectrum_widget else None),
            passed=spectrum_widget is not None and spectrum_widget.property("yellowCurveMode") == "true",
        ),
        LayoutMetricCheck(
            name="scan_stats_panel_visible",
            expected="scan stats panel visible",
            actual=f"visible={stats.isVisible() if stats else False}",
            passed=stats is not None and stats.isVisible(),
        ),
        LayoutMetricCheck(
            name="scan_stats_demo_values",
            expected="seeded runtime stat values",
            actual=shell.bottom_dock._runtime_stat_labels.get("current_freq", QLabel()).text(),
            passed=shell.bottom_dock._runtime_stat_labels.get("current_freq", QLabel()).text() == "2.450 GHz",
        ),
        LayoutMetricCheck(
            name="log_panel_visible",
            expected="log panel visible with >= 6 lines",
            actual=f"lines={log_lines}",
            passed=log_panel is not None and log_panel.isVisible() and log_lines >= 6,
        ),
        LayoutMetricCheck(
            name="log_category_tags",
            expected="INFO/WARN/ERROR/SCAN/DATA tags",
            actual=str(log_tags),
            passed=log_tags,
        ),
        LayoutMetricCheck(
            name="pcb_like_mock_board",
            expected="photo layer mock board loaded",
            actual="photo_layer_ready",
            passed=realtime.layer_manager.ensure_layer(LayerKind.PHOTO).canvas_width > 0,
        ),
        LayoutMetricCheck(
            name="heatmap_smooth_mode",
            expected="heatmap overlay enabled",
            actual=str(len(realtime.layer_manager.ensure_layer(LayerKind.HEATMAP).items())),
            passed=len(realtime.layer_manager.ensure_layer(LayerKind.HEATMAP).items()) > 0,
        ),
        LayoutMetricCheck(
            name="roi_control_points_visible",
            expected="ROI overlay items present",
            actual=str(len(roi_items)),
            passed=len(roi_items) >= 5,
        ),
        LayoutMetricCheck(
            name="right_panel_no_horizontal_clip",
            expected="property panel fits viewport width",
            actual=str(not shell.property_panel.has_horizontal_clipping()),
            passed=not shell.property_panel.has_horizontal_clipping(),
        ),
    ]

    progress = shell.findChild(QProgressBar, "commercialScanProgressBar")
    checks.append(
        LayoutMetricCheck(
            name="scan_progress_bar_visible",
            expected="runtime progress bar in dock",
            actual=f"visible={progress.isVisible() if progress else False}",
            passed=progress is not None and progress.isVisible(),
        )
    )

    axis = shell.findChild(QFrame, "canvasAxisLegend")
    cursor_hud = shell.findChild(QFrame, "canvasCursorHud")
    checks.extend(
        [
            LayoutMetricCheck(
                name="canvas_axis_legend",
                expected="axis legend visible",
                actual=f"visible={axis.isVisible() if axis else False}",
                passed=axis is not None and axis.isVisible(),
            ),
            LayoutMetricCheck(
                name="canvas_cursor_hud",
                expected="cursor HUD visible",
                actual=f"visible={cursor_hud.isVisible() if cursor_hud else False}",
                passed=cursor_hud is not None and cursor_hud.isVisible(),
            ),
        ]
    )

    minimap_title = shell.findChild(QLabel, "commercialMiniMapTitle")
    checks.append(
        LayoutMetricCheck(
            name="minimap_title_visible",
            expected='MiniMap title "全局视图"',
            actual=minimap_title.text() if minimap_title else "",
            passed=minimap_title is not None and "全局视图" in minimap_title.text(),
        )
    )

    return checks
