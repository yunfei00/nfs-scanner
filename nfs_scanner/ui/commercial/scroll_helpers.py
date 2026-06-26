"""Scrollbar tuning helpers for commercial UI widgets."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QScrollArea,
    QScrollBar,
    QWidget,
)

COMMERCIAL_SCROLLBAR_WIDTH = 14


def tune_scroll_bar(scroll_bar: QScrollBar) -> None:
    """Apply consistent step sizes so dragging feels smooth, not jumpy."""

    scroll_bar.setTracking(True)
    if scroll_bar.orientation() == Qt.Orientation.Vertical:
        scroll_bar.setSingleStep(8)
        scroll_bar.setPageStep(80)
    else:
        scroll_bar.setSingleStep(12)
        scroll_bar.setPageStep(100)


def configure_scroll_area(
    area: QScrollArea,
    *,
    vertical: bool = True,
    horizontal: bool = False,
) -> None:
    """Ensure a scroll area exposes usable vertical/horizontal bars."""

    area.setVerticalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAsNeeded if vertical else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )
    area.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAsNeeded if horizontal else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )
    if vertical and area.verticalScrollBar() is not None:
        tune_scroll_bar(area.verticalScrollBar())
    if horizontal and area.horizontalScrollBar() is not None:
        tune_scroll_bar(area.horizontalScrollBar())


def configure_abstract_scroll_area(widget: QAbstractScrollArea) -> None:
    """Tune scroll bars on plain text, list, table, and graphics views."""

    if widget.verticalScrollBar() is not None:
        tune_scroll_bar(widget.verticalScrollBar())
    if widget.horizontalScrollBar() is not None:
        tune_scroll_bar(widget.horizontalScrollBar())


def apply_commercial_scroll_config(root: QWidget) -> None:
    """Walk the commercial shell subtree and tune all scroll bars."""

    for scroll_area in root.findChildren(QScrollArea):
        configure_scroll_area(
            scroll_area,
            vertical=scroll_area.verticalScrollBarPolicy() != Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            horizontal=scroll_area.horizontalScrollBarPolicy() != Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )

    for scroll_widget in root.findChildren(QAbstractScrollArea):
        if isinstance(scroll_widget, QScrollArea):
            continue
        configure_abstract_scroll_area(scroll_widget)
