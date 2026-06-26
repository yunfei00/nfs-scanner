"""Layout metric collectors for commercial UI visual verification."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from PySide6.QtWidgets import QApplication, QMainWindow


@dataclass(slots=True)
class LayoutMetricCheck:
    """One layout assertion with pass/fail."""

    name: str
    expected: str
    actual: str
    passed: bool


@dataclass(slots=True)
class CommercialLayoutMetrics:
    """Measured commercial shell layout values."""

    uses_custom_title_bar: bool = False
    title_bar_height: int = 0
    bottom_dock_height: int = 0
    log_view_height: int = 0
    statistics_panel_height: int = 0
    left_panel_width: int = 0
    right_panel_width: int = 0
    workspace_width: int = 0
    canvas_width: int = 0
    canvas_height: int = 0
    canvas_to_right_ratio: float = 0.0
    canvas_to_left_ratio: float = 0.0
    canvas_view_area_ratio: float = 0.0
    colorbar_gap_px: int = 0
    toolbar_overflow: bool = False
    status_bar_visible: bool = False
    window_width: int = 0
    window_height: int = 0
    screen_available_width: int = 0
    screen_available_height: int = 0
    is_maximized: bool = False
    workflow_panel_height: int = 0
    device_status_panel_height: int = 0
    device_status_collapsed_height: int = 0
    device_status_has_inner_scroll: bool = False
    property_tab_bar_visible_after_scroll: bool = False
    numeric_field_line_edit_min_width: int = 0
    numeric_field_total_min_width: int = 0
    action_buttons_count: int = 0
    action_buttons_overlap: bool = False
    action_buttons_clipped: bool = False
    realtime_toolbar_min_button_width: int = 0
    realtime_toolbar_has_ellipsis: bool = False
    lut_combo_count: int = 0
    lut_combos_include_common: bool = False
    scroll_usability: dict = field(default_factory=dict)
    checks: list[LayoutMetricCheck] = field(default_factory=list)

    def all_passed(self) -> bool:
        return all(item.passed for item in self.checks)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["checks"] = [asdict(item) for item in self.checks]
        payload["all_passed"] = self.all_passed()
        return payload


def _between(value: int, low: int, high: int) -> bool:
    return low <= value <= high


def collect_layout_metrics(shell: QMainWindow) -> CommercialLayoutMetrics:
    """Measure key widget geometries from a visible commercial shell."""

    from PySide6.QtWidgets import QComboBox, QScrollArea, QTabWidget, QToolButton

    from nfs_scanner.ui.commercial.lut_presets import COMMON_LUT_NAMES
    from nfs_scanner.ui.commercial.top_header_metrics import OVERFLOW_FORBIDDEN_WIDTH
    from nfs_scanner.ui.commercial.main_shell import CommercialMainShell
    from nfs_scanner.ui.commercial.widgets import NFSCollapsiblePanel, NFSNumericField

    if not isinstance(shell, CommercialMainShell):
        raise TypeError("Expected CommercialMainShell instance")

    realtime = shell.workspace.realtime_view()
    canvas = realtime.canvas
    colorbar = realtime.color_bar
    view_area = max(realtime.width() * realtime.height(), 1)
    canvas_area = max(canvas.width() * canvas.height(), 0)

    canvas_global = canvas.mapToGlobal(canvas.rect().topLeft())
    colorbar_global = colorbar.mapToGlobal(colorbar.rect().topLeft())
    colorbar_gap = max(colorbar_global.x() - (canvas_global.x() + canvas.width()), 0)

    metrics = CommercialLayoutMetrics(
        uses_custom_title_bar=shell.uses_custom_title_bar(),
        title_bar_height=shell.title_bar.height(),
        bottom_dock_height=shell.bottom_dock.height(),
        left_panel_width=shell.left_scroll_area.width(),
        right_panel_width=shell.property_panel.width(),
        workspace_width=shell.workspace.width(),
        canvas_width=canvas.width(),
        canvas_height=canvas.height(),
        canvas_to_right_ratio=canvas.width() / max(shell.property_panel.width(), 1),
        canvas_to_left_ratio=canvas.width() / max(shell.left_scroll_area.width(), 1),
        canvas_view_area_ratio=canvas_area / view_area,
        colorbar_gap_px=colorbar_gap,
        toolbar_overflow=(
            shell.toolbar.is_overflow_visible() and shell.width() >= OVERFLOW_FORBIDDEN_WIDTH
        ),
        status_bar_visible=shell.status_bar_widget.is_fully_visible(),
        window_width=shell.width(),
        window_height=shell.height(),
        is_maximized=shell.is_custom_maximized() or shell.isMaximized(),
        workflow_panel_height=shell.workflow_panel.height(),
    )

    device_area = shell.findChild(QScrollArea, "commercialDeviceScroll")
    metrics.device_status_has_inner_scroll = device_area is not None
    device_panel = shell.device_status_panel.findChild(NFSCollapsiblePanel)
    if device_panel is not None and device_panel.is_expanded():
        body = getattr(device_panel, "_body_widget", None)
        metrics.device_status_panel_height = (
            body.sizeHint().height() + 48 if body is not None else device_panel.sizeHint().height()
        )
    else:
        metrics.device_status_panel_height = shell.device_status_panel.height()
    if device_panel is not None:
        was_expanded = device_panel.is_expanded()
        device_panel.set_expanded(False)
        if hasattr(shell, "_refresh_left_area_layout"):
            shell._refresh_left_area_layout()
        QApplication.processEvents()
        metrics.device_status_collapsed_height = shell.device_status_panel.height()
        device_panel.set_expanded(was_expanded)
        if hasattr(shell, "_refresh_left_area_layout"):
            shell._refresh_left_area_layout()
        QApplication.processEvents()

    property_tabs = shell.property_panel.findChild(QTabWidget, "commercialPropertyTabs")
    if property_tabs is not None:
        current_page = property_tabs.currentWidget()
        if isinstance(current_page, QScrollArea):
            scroll_bar = current_page.verticalScrollBar()
            previous = scroll_bar.value()
            scroll_bar.setValue(scroll_bar.maximum())
            QApplication.processEvents()
            tab_bar = property_tabs.tabBar()
            tab_rect = tab_bar.geometry()
            metrics.property_tab_bar_visible_after_scroll = (
                tab_bar.isVisible()
                and tab_rect.top() >= 0
                and tab_rect.bottom() <= property_tabs.height()
            )
            scroll_bar.setValue(previous)
            QApplication.processEvents()

    numeric_fields = shell.property_panel.findChildren(NFSNumericField)
    if numeric_fields:
        metrics.numeric_field_line_edit_min_width = min(
            field.line_edit().minimumWidth() for field in numeric_fields
        )
        metrics.numeric_field_total_min_width = min(field.minimumWidth() for field in numeric_fields)

    action_buttons = [
        shell.property_panel._start_scan_button,
        shell.property_panel._pause_scan_button,
        shell.property_panel._stop_scan_button,
    ]
    metrics.action_buttons_count = sum(button is not None for button in action_buttons)
    pause_button = shell.property_panel._pause_scan_button
    previous_pause_visible = pause_button.isVisible() if pause_button is not None else False
    previous_pause_text = pause_button.text() if pause_button is not None else ""
    previous_pause_enabled = pause_button.isEnabled() if pause_button is not None else True
    if pause_button is not None:
        shell.property_panel.set_pause_button_state(visible=True, paused=False)
        QApplication.processEvents()
    visible_action_buttons = [button for button in action_buttons if button is not None and button.isVisible()]
    metrics.action_buttons_overlap = any(
        left.geometry().intersects(right.geometry())
        for index, left in enumerate(visible_action_buttons)
        for right in visible_action_buttons[index + 1 :]
    )
    action_row = getattr(shell.property_panel, "_action_button_row", None)
    if action_row is not None:
        metrics.action_buttons_clipped = any(
            button.geometry().left() < 0
            or button.geometry().right() > action_row.contentsRect().right()
            or button.geometry().top() < 0
            or button.geometry().bottom() > action_row.contentsRect().bottom()
            for button in visible_action_buttons
        )
    if pause_button is not None:
        pause_button.setVisible(previous_pause_visible)
        pause_button.setText(previous_pause_text)
        pause_button.setEnabled(previous_pause_enabled)
        if hasattr(shell.property_panel, "_refresh_action_button_layout"):
            shell.property_panel._refresh_action_button_layout()
        QApplication.processEvents()

    realtime_buttons = shell.workspace.realtime_view().findChildren(QToolButton, "realtimeCanvasToolButton")
    if realtime_buttons:
        metrics.realtime_toolbar_min_button_width = min(button.width() for button in realtime_buttons)
        metrics.realtime_toolbar_has_ellipsis = any(
            button.text().strip() in {"...", "…"} or "..." in button.text()
            for button in realtime_buttons
        )

    common_lut_names = set(COMMON_LUT_NAMES)
    lut_combo_items: list[set[str]] = []
    for combo in shell.findChildren(QComboBox):
        items = {combo.itemText(index) for index in range(combo.count())}
        if "Turbo" in items or "Jet" in items:
            lut_combo_items.append(items)
    metrics.lut_combo_count = len(lut_combo_items)
    metrics.lut_combos_include_common = (
        len(lut_combo_items) >= 2
        and all(common_lut_names.issubset(items) for items in lut_combo_items)
    )

    screen = shell.screen() or QApplication.primaryScreen()
    if screen is not None:
        available = screen.availableGeometry()
        metrics.screen_available_width = available.width()
        metrics.screen_available_height = available.height()

    shell.toolbar.update_compact_mode(shell.width())
    metrics.toolbar_overflow = (
        shell.toolbar.is_overflow_visible() and shell.width() >= OVERFLOW_FORBIDDEN_WIDTH
    )

    log_view = shell.bottom_dock.log_view_widget()
    shell.bottom_dock.switch_to_logs_tab()
    QApplication.processEvents()
    if log_view is not None:
        metrics.log_view_height = log_view.height()

    shell.bottom_dock.switch_to_statistics_tab()
    QApplication.processEvents()
    metrics.statistics_panel_height = shell.bottom_dock.statistics_content_height()
    shell.bottom_dock.switch_to_logs_tab()
    QApplication.processEvents()

    from nfs_scanner.ui.commercial.scroll_metrics import collect_scroll_usability_metrics
    from nfs_scanner.ui.commercial.target_alignment_metrics import collect_target_alignment_checks

    from nfs_scanner.ui.commercial.top_header_metrics import collect_top_header_checks

    metrics.checks = _build_checks(metrics)
    metrics.checks.extend(collect_target_alignment_checks(shell))
    metrics.checks.extend(collect_top_header_checks(shell))

    scroll_metrics = collect_scroll_usability_metrics(shell)
    for scroll_check in scroll_metrics.checks:
        metrics.checks.append(
            LayoutMetricCheck(
                name=scroll_check.name,
                expected=scroll_check.expected,
                actual=scroll_check.actual,
                passed=scroll_check.passed,
            )
        )
    metrics.scroll_usability = scroll_metrics.to_dict()
    return metrics


def _build_checks(metrics: CommercialLayoutMetrics) -> list[LayoutMetricCheck]:
    compact_screen = metrics.screen_available_height <= 768 or metrics.window_height <= 768
    dock_min_required = 200 if compact_screen else 240
    log_min_required = 100 if compact_screen else 120
    stats_min_required = 100 if compact_screen else 120
    canvas_min_height = 240 if compact_screen else (360 if metrics.is_maximized else 280)

    checks = [
        LayoutMetricCheck(
            name="custom_title_bar",
            expected="frameless + title bar visible",
            actual=f"custom={metrics.uses_custom_title_bar}, height={metrics.title_bar_height}px",
            passed=metrics.uses_custom_title_bar and _between(metrics.title_bar_height, 48, 58),
        ),
        LayoutMetricCheck(
            name="title_bar_height",
            expected="48–58 px",
            actual=f"{metrics.title_bar_height}px",
            passed=_between(metrics.title_bar_height, 48, 58),
        ),
        LayoutMetricCheck(
            name="bottom_dock_height",
            expected=f">= {dock_min_required} px",
            actual=f"{metrics.bottom_dock_height}px",
            passed=metrics.bottom_dock_height >= dock_min_required,
        ),
        LayoutMetricCheck(
            name="log_view_height",
            expected=f">= {log_min_required} px",
            actual=f"{metrics.log_view_height}px",
            passed=metrics.log_view_height >= log_min_required,
        ),
        LayoutMetricCheck(
            name="statistics_panel_height",
            expected=f">= {stats_min_required} px",
            actual=f"{metrics.statistics_panel_height}px",
            passed=metrics.statistics_panel_height >= stats_min_required,
        ),
        LayoutMetricCheck(
            name="canvas_size",
            expected=f"height >= {canvas_min_height}px",
            actual=f"{metrics.canvas_width}x{metrics.canvas_height}px",
            passed=metrics.canvas_height >= canvas_min_height and metrics.canvas_width >= 320,
        ),
        LayoutMetricCheck(
            name="colorbar_adjacent",
            expected="gap <= 12 px",
            actual=f"{metrics.colorbar_gap_px}px",
            passed=metrics.colorbar_gap_px <= 12,
        ),
        LayoutMetricCheck(
            name="right_panel_width",
            expected="340–380 px",
            actual=f"{metrics.right_panel_width}px",
            passed=_between(metrics.right_panel_width, 340, 380),
        ),
        LayoutMetricCheck(
            name="left_panel_width",
            expected="220–280 px",
            actual=f"{metrics.left_panel_width}px",
            passed=_between(metrics.left_panel_width, 220, 280),
        ),
        LayoutMetricCheck(
            name="workflow_panel_height",
            expected="<= 360 px",
            actual=f"{metrics.workflow_panel_height}px",
            passed=metrics.workflow_panel_height <= 360,
        ),
        LayoutMetricCheck(
            name="device_status_panel_height",
            expected="expanded content height 120-650 px in left scroll",
            actual=f"{metrics.device_status_panel_height}px",
            passed=120 <= metrics.device_status_panel_height <= 650,
        ),
        LayoutMetricCheck(
            name="left_no_nested_device_scroll",
            expected="no isolated device-status scroll area",
            actual=f"inner_scroll={metrics.device_status_has_inner_scroll}",
            passed=not metrics.device_status_has_inner_scroll,
        ),
        LayoutMetricCheck(
            name="device_status_collapsed_height",
            expected="collapsed height <= 100 px",
            actual=f"{metrics.device_status_collapsed_height}px",
            passed=0 < metrics.device_status_collapsed_height <= 100,
        ),
        LayoutMetricCheck(
            name="property_tab_bar_fixed",
            expected="tab bar visible after content scroll",
            actual=str(metrics.property_tab_bar_visible_after_scroll),
            passed=metrics.property_tab_bar_visible_after_scroll,
        ),
        LayoutMetricCheck(
            name="numeric_field_line_edit_width",
            expected=">= 48 px",
            actual=f"{metrics.numeric_field_line_edit_min_width}px",
            passed=metrics.numeric_field_line_edit_min_width >= 48,
        ),
        LayoutMetricCheck(
            name="numeric_field_total_width",
            expected=">= 80 px",
            actual=f"{metrics.numeric_field_total_min_width}px",
            passed=metrics.numeric_field_total_min_width >= 80,
        ),
        LayoutMetricCheck(
            name="scan_action_buttons_layout",
            expected="start/pause/stop present with no overlap or clipping",
            actual=(
                f"count={metrics.action_buttons_count}, "
                f"overlap={metrics.action_buttons_overlap}, "
                f"clipped={metrics.action_buttons_clipped}"
            ),
            passed=(
                metrics.action_buttons_count == 3
                and not metrics.action_buttons_overlap
                and not metrics.action_buttons_clipped
            ),
        ),
        LayoutMetricCheck(
            name="realtime_toolbar_button_text",
            expected='no "..." labels and width >= 44 px',
            actual=(
                f"min_width={metrics.realtime_toolbar_min_button_width}px, "
                f"ellipsis={metrics.realtime_toolbar_has_ellipsis}"
            ),
            passed=(
                metrics.realtime_toolbar_min_button_width >= 44
                and not metrics.realtime_toolbar_has_ellipsis
            ),
        ),
        LayoutMetricCheck(
            name="lut_combo_common_presets",
            expected="realtime and display LUT combos include Jet/common presets",
            actual=(
                f"count={metrics.lut_combo_count}, "
                f"include_common={metrics.lut_combos_include_common}"
            ),
            passed=metrics.lut_combos_include_common,
        ),
        LayoutMetricCheck(
            name="center_canvas_priority",
            expected="canvas >= 1.6x right, >= 2.0x left, area >= 50%",
            actual=(
                f"right={metrics.canvas_to_right_ratio:.2f}x, "
                f"left={metrics.canvas_to_left_ratio:.2f}x, "
                f"area={metrics.canvas_view_area_ratio:.0%}"
            ),
            passed=(
                metrics.canvas_to_right_ratio >= 1.6
                and metrics.canvas_to_left_ratio >= 2.0
                and metrics.canvas_view_area_ratio >= 0.50
            ),
        ),
        LayoutMetricCheck(
            name="workspace_wider_than_right_panel",
            expected="workspace > right panel",
            actual=f"{metrics.workspace_width}px > {metrics.right_panel_width}px",
            passed=metrics.workspace_width > metrics.right_panel_width,
        ),
        LayoutMetricCheck(
            name="toolbar_no_overflow",
            expected="toolbar fits layout",
            actual=f"overflow={metrics.toolbar_overflow}",
            passed=not metrics.toolbar_overflow,
        ),
        LayoutMetricCheck(
            name="status_bar_visible",
            expected="status bar visible",
            actual=str(metrics.status_bar_visible),
            passed=metrics.status_bar_visible,
        ),
    ]

    if not metrics.is_maximized:
        checks.append(
            LayoutMetricCheck(
                name="default_window_within_screen",
                expected="window <= available screen",
                actual=(
                    f"{metrics.window_width}x{metrics.window_height} "
                    f"<= {metrics.screen_available_width}x{metrics.screen_available_height}"
                ),
                passed=(
                    metrics.window_width <= metrics.screen_available_width
                    and metrics.window_height <= metrics.screen_available_height
                ),
            )
        )
    else:
        checks.append(
            LayoutMetricCheck(
                name="maximized_window",
                expected="custom maximized == True",
                actual=str(metrics.is_maximized),
                passed=metrics.is_maximized,
            )
        )

    return checks
