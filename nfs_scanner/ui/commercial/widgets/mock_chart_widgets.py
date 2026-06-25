"""Lightweight mock chart widgets using QPainter (no extra deps)."""

from __future__ import annotations

import math
import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget


class MockSpectrumWidget(QWidget):
    """Simple mock spectrum curve for bottom dock and data view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("mockSpectrumWidget")
        self.setMinimumHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._view_mode = "trace"
        self._seed = random.randint(0, 9999)

    def set_view_mode(self, mode: str) -> None:
        self._view_mode = mode if mode in ("trace", "frequency") else "trace"
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)
        painter.fillRect(rect, QColor("#0B1220"))

        grid_pen = QPen(QColor("#2A3A52"), 1, Qt.PenStyle.DotLine)
        painter.setPen(grid_pen)
        for ratio in (0.25, 0.5, 0.75):
            y_value = rect.top() + rect.height() * ratio
            painter.drawLine(rect.left(), int(y_value), rect.right(), int(y_value))

        points: list[tuple[float, float]] = []
        count = 48
        for index in range(count):
            x_ratio = index / max(count - 1, 1)
            phase = self._seed * 0.01
            if self._view_mode == "frequency":
                wave = math.sin(x_ratio * math.pi * 4 + phase) * 0.35
                peak = math.exp(-((x_ratio - 0.62) ** 2) / 0.004) * 0.55
                value = 0.35 + wave + peak
            else:
                wave = math.sin(x_ratio * math.pi * 6 + phase) * 0.25
                value = 0.45 + wave + math.sin(x_ratio * 18) * 0.08
            points.append((rect.left() + x_ratio * rect.width(), rect.bottom() - value * rect.height()))

        curve_pen = QPen(QColor("#06D6E8"), 2)
        painter.setPen(curve_pen)
        for index in range(1, len(points)):
            x1, y1 = points[index - 1]
            x2, y2 = points[index]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        painter.setPen(QPen(QColor("#AAB7C8")))
        label = "Mock Trace" if self._view_mode == "trace" else "Mock Frequency"
        painter.drawText(rect.adjusted(4, 4, 0, 0), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, label)
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
