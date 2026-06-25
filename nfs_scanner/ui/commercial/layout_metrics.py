"""Layout metric collectors for commercial UI visual verification."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QWidget


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
    window_width: int = 0
    window_height: int = 0
    screen_available_width: int = 0
    screen_available_height: int = 0
    is_maximized: bool = False
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

    metrics = CommercialLayoutMetrics(
        uses_custom_title_bar=shell.uses_custom_title_bar(),
        title_bar_height=shell.title_bar.height(),
        bottom_dock_height=shell.bottom_dock.height(),
        left_panel_width=shell.left_scroll_area.width(),
        right_panel_width=shell.property_panel.width(),
        workspace_width=shell.workspace.width(),
        window_width=shell.width(),
        window_height=shell.height(),
        is_maximized=shell.is_custom_maximized() or shell.isMaximized(),
    )

    screen = shell.screen() or QApplication.primaryScreen()
    if screen is not None:
        available = screen.availableGeometry()
        metrics.screen_available_width = available.width()
        metrics.screen_available_height = available.height()

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
    return metrics


def _build_checks(metrics: CommercialLayoutMetrics) -> list[LayoutMetricCheck]:
    compact_screen = metrics.screen_available_height <= 768 or metrics.window_height <= 768
    dock_min_required = 195 if compact_screen else 200
    log_min_required = 100 if compact_screen else 120
    stats_min_required = 100 if compact_screen else 120

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
            name="right_panel_width",
            expected="320–460 px",
            actual=f"{metrics.right_panel_width}px",
            passed=_between(metrics.right_panel_width, 320, 460),
        ),
        LayoutMetricCheck(
            name="left_panel_width",
            expected="240–330 px",
            actual=f"{metrics.left_panel_width}px",
            passed=_between(metrics.left_panel_width, 240, 330),
        ),
        LayoutMetricCheck(
            name="workspace_wider_than_right_panel",
            expected="workspace > right panel",
            actual=f"{metrics.workspace_width}px > {metrics.right_panel_width}px",
            passed=metrics.workspace_width > metrics.right_panel_width,
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
                expected="isMaximized() == True",
                actual=str(metrics.is_maximized),
                passed=metrics.is_maximized,
            )
        )

    return checks
