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

    from nfs_scanner.ui.commercial.main_shell import CommercialMainShell

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
        toolbar_overflow=shell.toolbar.has_layout_overflow(),
        status_bar_visible=shell.status_bar_widget.is_fully_visible(),
        window_width=shell.width(),
        window_height=shell.height(),
        is_maximized=shell.is_custom_maximized() or shell.isMaximized(),
    )

    screen = shell.screen() or QApplication.primaryScreen()
    if screen is not None:
        available = screen.availableGeometry()
        metrics.screen_available_width = available.width()
        metrics.screen_available_height = available.height()

    shell.toolbar.update_compact_mode(shell.width())

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

    metrics.checks = _build_checks(metrics)

    from nfs_scanner.ui.commercial.scroll_metrics import collect_scroll_usability_metrics

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
    dock_min_required = 195 if compact_screen else 200
    log_min_required = 100 if compact_screen else 120
    stats_min_required = 100 if compact_screen else 120
    canvas_min_height = 240 if compact_screen else (360 if metrics.is_maximized else 280)

    checks = [
        LayoutMetricCheck(
            name="custom_title_bar",
            expected="frameless + title bar visible",
            actual=f"custom={metrics.uses_custom_title_bar}, height={metrics.title_bar_height}px",
            passed=metrics.uses_custom_title_bar and _between(metrics.title_bar_height, 28, 44),
        ),
        LayoutMetricCheck(
            name="title_bar_height",
            expected="28–44 px",
            actual=f"{metrics.title_bar_height}px",
            passed=_between(metrics.title_bar_height, 28, 44),
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
            expected="300–380 px",
            actual=f"{metrics.right_panel_width}px",
            passed=_between(metrics.right_panel_width, 300, 380),
        ),
        LayoutMetricCheck(
            name="left_panel_width",
            expected="220–280 px",
            actual=f"{metrics.left_panel_width}px",
            passed=_between(metrics.left_panel_width, 220, 280),
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
