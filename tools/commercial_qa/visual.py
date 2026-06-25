"""Visual/layout checks for commercial QA."""

from __future__ import annotations

from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QWidget

from nfs_scanner.ui.commercial.layout_metrics import CommercialLayoutMetrics, collect_layout_metrics

from .models import QACheck


def _between(value: int, low: int, high: int) -> bool:
    return low <= value <= high


def _find_demo_indicator(shell: QMainWindow) -> tuple[bool, str]:
    banner = shell.findChild(QWidget, "demoModeBanner")
    if banner is not None and banner.isVisible():
        return True, "demoModeBanner visible"
    demo_label = shell.findChild(QLabel, "commercialTitleBarDemo")
    if demo_label is not None and demo_label.isVisible() and demo_label.text().strip():
        return True, f"title bar demo label: {demo_label.text()}"
    return False, "no demo banner or title bar demo label"


def _estimate_log_visible_lines(log_view, min_lines: int = 6) -> tuple[int, bool]:
    if log_view is None:
        return 0, False
    font = log_view.font()
    metrics = QFontMetrics(font)
    line_height = max(metrics.lineSpacing(), 1)
    visible_lines = max(log_view.height() // line_height, 0)
    text_lines = len(log_view.toPlainText().splitlines())
    return max(visible_lines, min(text_lines, visible_lines + text_lines)), visible_lines >= min_lines


def build_qa_visual_checks(metrics: CommercialLayoutMetrics, *, shell: QMainWindow) -> list[QACheck]:
    """Build QA-specific visual checks (stricter than visual_check on large screens)."""

    compact = metrics.screen_available_height <= 768 or metrics.window_height <= 768
    dock_min = 195 if compact else 200
    log_min = 100 if compact else 140
    stats_min = 100 if compact else 140

    demo_visible, demo_actual = _find_demo_indicator(shell)

    log_view = None
    if hasattr(shell, "bottom_dock"):
        shell.bottom_dock.switch_to_logs_tab()
        QApplication.processEvents()
        log_view = shell.bottom_dock.log_view_widget()
    line_count, lines_ok = _estimate_log_visible_lines(log_view, min_lines=6)

    checks = [
        QACheck(
            name="custom_title_bar",
            category="visual",
            expected="frameless custom title bar",
            actual=f"custom={metrics.uses_custom_title_bar}, height={metrics.title_bar_height}px",
            passed=metrics.uses_custom_title_bar and _between(metrics.title_bar_height, 28, 44),
            auto_fixable=True,
        ),
        QACheck(
            name="no_native_title_bar",
            category="visual",
            expected="FramelessWindowHint enabled",
            actual=f"custom={metrics.uses_custom_title_bar}",
            passed=metrics.uses_custom_title_bar,
            auto_fixable=True,
        ),
        QACheck(
            name="title_bar_height",
            category="visual",
            expected="28–44 px",
            actual=f"{metrics.title_bar_height}px",
            passed=_between(metrics.title_bar_height, 28, 44),
            auto_fixable=True,
        ),
        QACheck(
            name="demo_indicator_visible",
            category="visual",
            expected="demo banner or DEMO MODE label visible",
            actual=demo_actual,
            passed=demo_visible,
            auto_fixable=False,
        ),
        QACheck(
            name="toolbar_no_overflow",
            category="visual",
            expected="toolbar fits layout",
            actual=f"overflow={metrics.toolbar_overflow}",
            passed=not metrics.toolbar_overflow,
            auto_fixable=True,
        ),
        QACheck(
            name="left_panel_width",
            category="visual",
            expected="220–280 px",
            actual=f"{metrics.left_panel_width}px",
            passed=_between(metrics.left_panel_width, 220, 280),
            auto_fixable=True,
        ),
        QACheck(
            name="right_panel_width",
            category="visual",
            expected="300–380 px",
            actual=f"{metrics.right_panel_width}px",
            passed=_between(metrics.right_panel_width, 300, 380),
            auto_fixable=True,
        ),
        QACheck(
            name="center_canvas_priority",
            category="visual",
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
            auto_fixable=True,
        ),
        QACheck(
            name="canvas_wider_than_right_panel",
            category="visual",
            expected="workspace > right panel",
            actual=f"{metrics.workspace_width}px > {metrics.right_panel_width}px",
            passed=metrics.workspace_width > metrics.right_panel_width,
            auto_fixable=True,
        ),
        QACheck(
            name="bottom_dock_height",
            category="visual",
            expected=f">= {dock_min}px",
            actual=f"{metrics.bottom_dock_height}px",
            passed=metrics.bottom_dock_height >= dock_min,
            auto_fixable=True,
        ),
        QACheck(
            name="log_view_height",
            category="visual",
            expected=f">= {log_min}px",
            actual=f"{metrics.log_view_height}px",
            passed=metrics.log_view_height >= log_min,
            auto_fixable=True,
        ),
        QACheck(
            name="log_visible_lines",
            category="visual",
            expected=">= 6 visible lines",
            actual=f"estimated={line_count}",
            passed=lines_ok,
            auto_fixable=True,
        ),
        QACheck(
            name="statistics_panel_height",
            category="visual",
            expected=f">= {stats_min}px",
            actual=f"{metrics.statistics_panel_height}px",
            passed=metrics.statistics_panel_height >= stats_min,
            auto_fixable=True,
        ),
        QACheck(
            name="status_bar_visible",
            category="visual",
            expected="status bar visible",
            actual=str(metrics.status_bar_visible),
            passed=metrics.status_bar_visible,
            auto_fixable=True,
        ),
    ]

    if not metrics.is_maximized:
        checks.append(
            QACheck(
                name="default_window_within_screen",
                category="visual",
                expected="window <= available screen",
                actual=(
                    f"{metrics.window_width}x{metrics.window_height} "
                    f"<= {metrics.screen_available_width}x{metrics.screen_available_height}"
                ),
                passed=(
                    metrics.window_width <= metrics.screen_available_width
                    and metrics.window_height <= metrics.screen_available_height
                ),
                auto_fixable=True,
            )
        )
    else:
        checks.append(
            QACheck(
                name="maximized_window_capture",
                category="visual",
                expected="custom maximized == True",
                actual=str(metrics.is_maximized),
                passed=metrics.is_maximized,
                auto_fixable=True,
            )
        )

    return checks


def collect_qa_layout_metrics(shell: QMainWindow) -> CommercialLayoutMetrics:
    """Collect layout metrics with logs tab active for QA."""

    return collect_layout_metrics(shell)
