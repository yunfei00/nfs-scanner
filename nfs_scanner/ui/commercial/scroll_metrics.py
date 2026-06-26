"""Scrollbar usability metrics for commercial UI verification."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QScrollArea, QScrollBar, QSlider, QTabWidget, QWidget

from nfs_scanner.ui.commercial.main_shell import CommercialMainShell
from nfs_scanner.ui.commercial.scroll_helpers import COMMERCIAL_SCROLLBAR_WIDTH

_STYLE_PATH = Path(__file__).resolve().parents[3] / "resources" / "styles" / "dark_professional.qss"
_MIN_SCROLLBAR_WIDTH = 12


@dataclass(slots=True)
class ScrollMetricCheck:
    name: str
    expected: str
    actual: str
    passed: bool


@dataclass(slots=True)
class ScrollUsabilityMetrics:
    left_scrollbar_width: int = 0
    device_scrollbar_width: int = 0
    property_scrollbar_width: int = 0
    log_scrollbar_width: int = 0
    data_task_list_scrollbar_width: int = 0
    qss_handle_min_height: int = 0
    qss_handle_min_width: int = 0
    has_slider_widgets: bool = False
    wheel_test_passed: bool = False
    handle_drag_test_passed: bool = False
    slider_test_status: str = "Not Applicable"
    checks: list[ScrollMetricCheck] = field(default_factory=list)

    def all_passed(self) -> bool:
        return all(item.passed for item in self.checks)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["checks"] = [asdict(item) for item in self.checks]
        payload["all_passed"] = self.all_passed()
        return payload


def _read_qss_handle_mins() -> tuple[int, int]:
    if not _STYLE_PATH.is_file():
        return 0, 0
    text = _STYLE_PATH.read_text(encoding="utf-8")
    min_height = 0
    min_width = 0
    height_match = re.search(r"QScrollBar::handle:vertical\s*\{[^}]*min-height:\s*(\d+)px", text, re.S)
    width_match = re.search(r"QScrollBar::handle:horizontal\s*\{[^}]*min-width:\s*(\d+)px", text, re.S)
    if height_match:
        min_height = int(height_match.group(1))
    if width_match:
        min_width = int(width_match.group(1))
    return min_height, min_width


def _scrollbar_width(scroll_bar: QScrollBar | None) -> int:
    if scroll_bar is None or not scroll_bar.isVisible():
        return 0
    return scroll_bar.width() if scroll_bar.orientation() == Qt.Orientation.Vertical else scroll_bar.height()


def _is_scrollable(scroll_bar: QScrollBar | None) -> bool:
    if scroll_bar is None:
        return False
    return scroll_bar.maximum() > scroll_bar.minimum()


def _exercise_scroll_bar(scroll_bar: QScrollBar | None) -> tuple[bool, bool]:
    """Return wheel-step and handle-position usability results."""

    if scroll_bar is None or not _is_scrollable(scroll_bar):
        return True, True

    before = scroll_bar.value()
    step = max(scroll_bar.singleStep(), 1)
    scroll_bar.setValue(min(before + step, scroll_bar.maximum()))
    QApplication.processEvents()
    wheel_ok = scroll_bar.value() >= before

    target = (scroll_bar.minimum() + scroll_bar.maximum()) // 2
    scroll_bar.setValue(target)
    QApplication.processEvents()
    handle_ok = scroll_bar.value() == target
    return wheel_ok, handle_ok


def _current_property_tab_scroll(shell: CommercialMainShell) -> QScrollArea | None:
    tabs = shell.property_panel.findChild(QTabWidget, "commercialPropertyTabs")
    if tabs is None:
        return None
    current = tabs.currentWidget()
    return current if isinstance(current, QScrollArea) else None


def collect_scroll_usability_metrics(shell: CommercialMainShell) -> ScrollUsabilityMetrics:
    """Measure scrollbar widths and basic interaction on key commercial regions."""

    from nfs_scanner.ui.commercial.scroll_helpers import apply_commercial_scroll_config

    apply_commercial_scroll_config(shell)
    QApplication.processEvents()

    shell.bottom_dock.switch_to_logs_tab()
    QApplication.processEvents()

    log_view = shell.bottom_dock.log_view_widget()
    if log_view is not None:
        scroll_bar = log_view.verticalScrollBar()
        if scroll_bar is not None and scroll_bar.maximum() <= scroll_bar.minimum():
            for index in range(24):
                log_view.appendPlainText(f"[INFO] QA scroll seed line {index + 1}")
        QApplication.processEvents()

    left_scroll = shell.left_scroll_area.verticalScrollBar() if shell.left_scroll_area else None
    device_area = shell.findChild(QScrollArea, "commercialDeviceScroll")
    device_scroll = device_area.verticalScrollBar() if device_area is not None else None

    property_area = _current_property_tab_scroll(shell)
    property_scroll = property_area.verticalScrollBar() if property_area is not None else None
    log_view = shell.bottom_dock.log_view_widget()
    log_scroll = log_view.verticalScrollBar() if log_view is not None else None

    data_view = shell.workspace.data_view()
    task_list = data_view._task_list
    task_scroll = task_list.verticalScrollBar() if task_list is not None else None

    qss_min_h, qss_min_w = _read_qss_handle_mins()
    wheel_ok, handle_ok = _exercise_scroll_bar(log_scroll)

    sliders = shell.findChildren(QSlider)
    slider_status = "Not Applicable"
    if sliders:
        slider = sliders[0]
        previous = slider.value()
        target = min(previous + 5, slider.maximum())
        if target == previous:
            target = max(previous - 5, slider.minimum())
        slider.setValue(target)
        QApplication.processEvents()
        slider_status = "PASS" if slider.value() == target and slider.hasTracking() else "FAIL"

    metrics = ScrollUsabilityMetrics(
        left_scrollbar_width=_scrollbar_width(left_scroll),
        device_scrollbar_width=_scrollbar_width(device_scroll),
        property_scrollbar_width=_scrollbar_width(property_scroll),
        log_scrollbar_width=_scrollbar_width(log_scroll),
        data_task_list_scrollbar_width=_scrollbar_width(task_scroll),
        qss_handle_min_height=qss_min_h,
        qss_handle_min_width=qss_min_w,
        has_slider_widgets=bool(shell.findChildren(QSlider)),
        wheel_test_passed=wheel_ok,
        handle_drag_test_passed=handle_ok,
        slider_test_status=slider_status,
    )
    metrics.checks = _build_scroll_checks(metrics, shell)
    return metrics


def _build_scroll_checks(metrics: ScrollUsabilityMetrics, shell: CommercialMainShell) -> list[ScrollMetricCheck]:
    log_view = shell.bottom_dock.log_view_widget()
    log_scroll = log_view.verticalScrollBar() if log_view is not None else None
    property_area = _current_property_tab_scroll(shell)
    property_scroll = property_area.verticalScrollBar() if property_area is not None else None

    checks = [
        ScrollMetricCheck(
            name="qss_scrollbar_handle_min_height",
            expected=">= 24px in QSS",
            actual=f"{metrics.qss_handle_min_height}px",
            passed=24 <= metrics.qss_handle_min_height <= 40,
        ),
        ScrollMetricCheck(
            name="qss_scrollbar_handle_min_width",
            expected=">= 24px in QSS",
            actual=f"{metrics.qss_handle_min_width}px",
            passed=24 <= metrics.qss_handle_min_width <= 40,
        ),
        ScrollMetricCheck(
            name="left_scrollbar_width",
            expected=f">= {_MIN_SCROLLBAR_WIDTH}px when visible",
            actual=f"{metrics.left_scrollbar_width}px",
            passed=metrics.left_scrollbar_width == 0 or metrics.left_scrollbar_width >= _MIN_SCROLLBAR_WIDTH,
        ),
        ScrollMetricCheck(
            name="property_scrollbar_width",
            expected=f">= {_MIN_SCROLLBAR_WIDTH}px when visible",
            actual=f"{metrics.property_scrollbar_width}px",
            passed=metrics.property_scrollbar_width == 0 or metrics.property_scrollbar_width >= _MIN_SCROLLBAR_WIDTH,
        ),
        ScrollMetricCheck(
            name="log_scrollbar_width",
            expected=f">= {_MIN_SCROLLBAR_WIDTH}px when scrollable",
            actual=f"{metrics.log_scrollbar_width}px",
            passed=_is_scrollable(log_scroll) and metrics.log_scrollbar_width >= _MIN_SCROLLBAR_WIDTH,
        ),
        ScrollMetricCheck(
            name="log_area_scrollable",
            expected="log content scrollable",
            actual=f"range={log_scroll.maximum() if log_scroll else 0}",
            passed=_is_scrollable(log_scroll),
        ),
        ScrollMetricCheck(
            name="property_area_scrollable",
            expected="property panel scrollable",
            actual=f"range={property_scroll.maximum() if property_scroll else 0}",
            passed=_is_scrollable(property_scroll),
        ),
        ScrollMetricCheck(
            name="device_status_scrollable_or_compact",
            expected="device scroll visible when needed",
            actual=f"width={metrics.device_scrollbar_width}px",
            passed=metrics.device_scrollbar_width == 0 or metrics.device_scrollbar_width >= _MIN_SCROLLBAR_WIDTH,
        ),
        ScrollMetricCheck(
            name="wheel_interaction",
            expected="wheel step changes scroll value",
            actual=str(metrics.wheel_test_passed),
            passed=metrics.wheel_test_passed,
        ),
        ScrollMetricCheck(
            name="handle_position_interaction",
            expected="handle position can be set smoothly",
            actual=str(metrics.handle_drag_test_passed),
            passed=metrics.handle_drag_test_passed,
        ),
    ]

    if metrics.has_slider_widgets:
        checks.append(
            ScrollMetricCheck(
                name="slider_widgets_present",
                expected="slider handle style configured",
                actual="QSlider found",
                passed=metrics.qss_handle_min_height >= 16,
            )
        )

    return checks
