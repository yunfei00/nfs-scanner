"""Mock pseudo-3D scan visualization using QPainter (no OpenGL)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QPolygon
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.mock_point_data import demo_sample_rows, rows_for_service

from ..widgets import NFSSecondaryButton, NFSCard

if TYPE_CHECKING:
    from nfs_scanner.core.mock_analysis_service import MockAnalysisService


class Mock3DCanvas(QWidget):
    """Lightweight isometric mock 3D surface."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("mock3DCanvas")
        self.setMinimumHeight(280)
        self._view_mode = "oblique"
        self._show_heatmap = True
        self._show_path = True
        self._rows = demo_sample_rows()
        self._title = "Demo Placeholder"

    def set_task_context(self, title: str, rows) -> None:
        self._title = title
        self._rows = rows
        self.update()

    def set_view_mode(self, mode: str) -> None:
        self._view_mode = mode
        self.update()

    def set_show_heatmap(self, visible: bool) -> None:
        self._show_heatmap = visible
        self.update()

    def set_show_path(self, visible: bool) -> None:
        self._show_path = visible
        self.update()

    def reset_view(self) -> None:
        self._view_mode = "oblique"
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1a1f2b"))

        w, h = self.width(), self.height()
        margin = 40
        board_w = w - margin * 2
        board_h = (h - margin * 2) * 0.55
        ox, oy = margin, h - margin - board_h * 0.3

        tilt = 0.35 if self._view_mode == "oblique" else 0.05
        if self._view_mode == "top":
            tilt = 0.02

        # PCB plane
        painter.setPen(QPen(QColor("#3d4f6a"), 2))
        painter.setBrush(QColor("#2a3344"))
        self._draw_quad(painter, ox, oy, board_w, board_h, tilt)

        # Scan region
        painter.setPen(QPen(QColor("#58a6ff"), 1, Qt.PenStyle.DashLine))
        inset = board_w * 0.15
        self._draw_quad(painter, ox + inset, oy + inset * 0.5, board_w * 0.7, board_h * 0.7, tilt)

        if self._show_heatmap and self._rows:
            grid = min(int(math.sqrt(len(self._rows))), 8)
            for index, row in enumerate(self._rows[: grid * grid]):
                gx = index % grid
                gy = index // grid
                norm = (row.amplitude + 90) / 60.0
                color = QColor.fromHsvF(0.65 - norm * 0.5, 0.8, 0.5 + norm * 0.4)
                cx = ox + inset + gx * (board_w * 0.7 / max(grid - 1, 1))
                cy = oy + inset * 0.5 + gy * (board_h * 0.7 / max(grid - 1, 1))
                bar_h = 8 + norm * 40
                self._draw_bar(painter, cx, cy, bar_h, color, tilt)

        if self._show_path and len(self._rows) >= 2:
            painter.setPen(QPen(QColor("#f0c040"), 2))
            points = []
            for index, row in enumerate(self._rows[: min(len(self._rows), 20)]):
                t = index / max(len(self._rows) - 1, 1)
                px = ox + inset + t * board_w * 0.7
                py = oy + inset * 0.5 + (index % 4) * (board_h * 0.15)
                points.append(self._iso(px, py, 12, tilt))
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])

        # Probe
        probe = self._iso(ox + board_w * 0.5, oy + board_h * 0.35, 20, tilt)
        px, py = probe.x(), probe.y()
        painter.setPen(QPen(QColor("#ff6b6b"), 2))
        painter.drawLine(px, py - 30, px, py)
        painter.setBrush(QColor("#ff6b6b"))
        painter.drawEllipse(px - 4, py - 34, 8, 8)

        # Axes labels
        painter.setPen(QColor("#9aa5b5"))
        painter.drawText(margin, 24, f"Mock 3D · {self._title}")
        painter.drawText(w - 120, h - 12, "X →")
        painter.drawText(8, h // 2, "Y ↑")
        painter.drawText(w - 48, 24, "Z")

    @staticmethod
    def _iso(x: float, y: float, z: float, tilt: float) -> QPoint:
        return QPoint(int(x + z * tilt), int(y - z))

    def _draw_quad(self, painter: QPainter, x, y, w, h, tilt) -> None:
        p1 = self._iso(x, y, 0, tilt)
        p2 = self._iso(x + w, y, 0, tilt)
        p3 = self._iso(x + w, y + h, 0, tilt)
        p4 = self._iso(x, y + h, 0, tilt)
        painter.drawPolygon(QPolygon([p1, p2, p3, p4]))

    def _draw_bar(self, painter: QPainter, x, y, height, color, tilt) -> None:
        base = self._iso(x, y, 0, tilt)
        top = self._iso(x, y, height, tilt)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawLine(base, top)
        painter.drawEllipse(top.x() - 3, top.y() - 3, 6, 6)


class ThreeDView(QWidget):
    """Mock 3D workspace tab."""

    status_message = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("threeDView")
        self._analysis: MockAnalysisService | None = None
        self._canvas = Mock3DCanvas(self)
        self._setup_ui()
        self.refresh_from_tasks()

    def bind_analysis(self, service: MockAnalysisService) -> None:
        self._analysis = service
        self.refresh_from_tasks()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QWidget(self)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        for label, slot in (
            ("俯视", lambda: self._set_view("top")),
            ("斜视", lambda: self._set_view("oblique")),
            ("重置", self._canvas.reset_view),
        ):
            button = NFSSecondaryButton(label, toolbar)
            button.clicked.connect(slot)
            toolbar_layout.addWidget(button)
        self._heatmap_check = QCheckBox("热力面", toolbar)
        self._heatmap_check.setChecked(True)
        self._heatmap_check.toggled.connect(self._canvas.set_show_heatmap)
        self._path_check = QCheckBox("路径", toolbar)
        self._path_check.setChecked(True)
        self._path_check.toggled.connect(self._canvas.set_show_path)
        toolbar_layout.addWidget(self._heatmap_check)
        toolbar_layout.addWidget(self._path_check)
        toolbar_layout.addStretch(1)
        hint = QLabel("Mock 伪 3D · 无 OpenGL", toolbar)
        hint.setObjectName("nfsMutedLabel")
        toolbar_layout.addWidget(hint)

        card = NFSCard("3D 扫描视图", self)
        card.body_layout.addWidget(self._canvas, 1)
        layout.addWidget(toolbar)
        layout.addWidget(card, 1)

    def _set_view(self, mode: str) -> None:
        self._canvas.set_view_mode(mode)
        self.status_message.emit("UI", f"3D 视图模式: {mode}")

    def refresh_from_tasks(self) -> None:
        if self._analysis is None:
            rows = demo_sample_rows()
            self._canvas.set_task_context("Demo Placeholder", rows)
            return
        tasks = self._analysis.list_tasks()
        if not tasks:
            self._canvas.set_task_context("Demo Placeholder", demo_sample_rows())
            return
        task = tasks[0]
        rows = rows_for_service(self._analysis, task.task_id)
        self._canvas.set_task_context(f"{task.name} ({task.point_count} pts)", rows)

    def has_content(self) -> bool:
        return self._canvas.height() > 0
