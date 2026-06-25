"""Marker graphics items with tooltip metadata."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem


@dataclass(slots=True)
class MarkerData:
    """Mock marker metadata shown in tooltips."""

    x: float
    y: float
    z: float
    frequency: str
    amplitude: str


class MarkerItem(QGraphicsEllipseItem):
    """Selectable marker that follows scene coordinates."""

    MARKER_SIZE = 12.0

    def __init__(self, data: MarkerData, parent=None) -> None:
        half = self.MARKER_SIZE / 2.0
        super().__init__(-half, -half, self.MARKER_SIZE, self.MARKER_SIZE, parent)
        self._data = data
        self.setPos(data.x, data.y)
        self.setBrush(QBrush(QColor("#F59E0B")))
        self.setPen(QPen(QColor("#E8EEF8"), 1.5))
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setToolTip(self._format_tooltip(data))
        self.setZValue(10.0)

    @property
    def data(self) -> MarkerData:
        return self._data

    def _format_tooltip(self, data: MarkerData) -> str:
        return (
            f"X: {data.x:.2f} mm\n"
            f"Y: {data.y:.2f} mm\n"
            f"Z: {data.z:.2f} mm\n"
            f"Frequency: {data.frequency}\n"
            f"Amplitude: {data.amplitude}"
        )

    def hoverEnterEvent(self, event) -> None:
        self.setPen(QPen(QColor("#0EA5FF"), 2.0))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self.setPen(QPen(QColor("#E8EEF8"), 1.5))
        super().hoverLeaveEvent(event)
