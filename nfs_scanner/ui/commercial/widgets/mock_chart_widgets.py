"""Lightweight mock chart widgets using QPainter (no extra deps)."""

from __future__ import annotations

import math
import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget


class MockSpectrumWidget(QWidget):
    """Target-style yellow spectrum curve with grid, marker, and axis labels."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("mockSpectrumWidget")
        self.setProperty("yellowCurveMode", "true")
        self.setMinimumHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._view_mode = "trace"
        self._seed = random.randint(0, 9999)
        self._marker_freq = 2.45

    def set_view_mode(self, mode: str) -> None:
        self._view_mode = mode if mode in ("trace", "frequency") else "trace"
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(6, 6, -6, -6)
        painter.fillRect(rect, QColor("#050A12"))

        grid_pen = QPen(QColor("#243247"), 1, Qt.PenStyle.SolidLine)
        painter.setPen(grid_pen)
        for ratio in (0.2, 0.4, 0.6, 0.8):
            y_value = rect.top() + rect.height() * ratio
            painter.drawLine(rect.left(), int(y_value), rect.right(), int(y_value))
        for ratio in (0.25, 0.5, 0.75):
            x_value = rect.left() + rect.width() * ratio
            painter.drawLine(int(x_value), rect.top(), int(x_value), rect.bottom())

        points: list[tuple[float, float]] = []
        count = 64
        peak_x = 0.58
        for index in range(count):
            x_ratio = index / max(count - 1, 1)
            noise = math.sin(x_ratio * math.pi * 8 + self._seed * 0.02) * 0.04
            baseline = 0.22 + math.sin(x_ratio * math.pi * 2) * 0.05
            peak = math.exp(-((x_ratio - peak_x) ** 2) / 0.0035) * 0.72
            shoulder = math.exp(-((x_ratio - 0.35) ** 2) / 0.02) * 0.18
            value = min(max(baseline + peak + shoulder + noise, 0.08), 0.95)
            points.append((rect.left() + x_ratio * rect.width(), rect.bottom() - value * rect.height()))

        curve_pen = QPen(QColor("#FACC15"), 2)
        painter.setPen(curve_pen)
        for index in range(1, len(points)):
            x1, y1 = points[index - 1]
            x2, y2 = points[index]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        marker_x = rect.left() + peak_x * rect.width()
        marker_y = rect.bottom() - 0.72 * rect.height()
        painter.setPen(QPen(QColor("#22C55E"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(marker_x), rect.top(), int(marker_x), rect.bottom())
        painter.setPen(QPen(QColor("#22C55E")))
        painter.setBrush(QColor("#22C55E"))
        painter.drawEllipse(int(marker_x - 4), int(marker_y - 4), 8, 8)
        painter.setPen(QPen(QColor("#E8EEF8")))
        font = QFont(painter.font())
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(int(marker_x + 6), int(marker_y + 4), "M1")

        painter.setPen(QPen(QColor("#69788D")))
        painter.drawText(rect.left(), rect.bottom() + 14, "1.000 GHz")
        painter.drawText(int(rect.center().x() - 24), rect.bottom() + 14, "2.450 GHz")
        painter.drawText(rect.right() - 56, rect.bottom() + 14, "6.000 GHz")
        painter.drawText(rect.left() - 2, rect.top() + 10, "0 dB")
        painter.drawText(rect.left() - 2, rect.bottom() - 4, "-100 dB")
        painter.end()


class MockHeatmapWidget(QWidget):
    """Grid heatmap preview using QPainter."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("mockHeatmapWidget")
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._title = "Mock Heatmap"
        self._grid_size = 8
        self._seed = random.randint(0, 9999)

    def set_task_context(self, *, title: str, point_count: int, view_mode: str) -> None:
        self._title = title
        self._grid_size = 8 if point_count >= 36 else 6
        self._seed = hash((title, view_mode, point_count)) & 0xFFFF
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)
        painter.fillRect(rect, QColor("#0B1220"))

        grid = self._grid_size
        cell_w = rect.width() / grid
        cell_h = rect.height() / grid
        rng = random.Random(self._seed)

        for row in range(grid):
            for col in range(grid):
                intensity = rng.uniform(0.15, 1.0)
                color = QColor.fromHsvF(0.58 - intensity * 0.15, 0.75, 0.35 + intensity * 0.55)
                x_value = rect.left() + col * cell_w
                y_value = rect.top() + row * cell_h
                painter.fillRect(int(x_value), int(y_value), int(cell_w) - 1, int(cell_h) - 1, color)

        painter.setPen(QPen(QColor("#AAB7C8")))
        painter.drawText(rect.adjusted(4, 4, 0, 0), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, self._title)
        painter.end()
