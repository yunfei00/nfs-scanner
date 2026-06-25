"""Mini map widget for large realtime canvases."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .realtime_canvas import RealtimeCanvas


class MiniMap(QWidget):
    """Small overview map with a viewport frame placeholder."""

    def __init__(self, canvas: RealtimeCanvas | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialMiniMap")
        self._canvas = canvas
        self.setMinimumSize(140, 100)
        self.setMaximumSize(180, 130)

    def bind_canvas(self, canvas: RealtimeCanvas) -> None:
        """Attach one realtime canvas for viewport updates."""

        self._canvas = canvas
        canvas.viewport().installEventFilter(self)
        self.update()

    def eventFilter(self, watched, event) -> bool:
        if watched is self._canvas.viewport() and event.type() in {
            QEvent.Type.Resize,
            QEvent.Type.Paint,
            QEvent.Type.Wheel,
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonRelease,
        }:
            self.update()
        return super().eventFilter(watched, event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#111A2B"))

        scene_rect = self._scene_rect()
        if scene_rect.isEmpty():
            painter.end()
            super().paintEvent(event)
            return

        map_rect = self.rect().adjusted(8, 8, -8, -8)
        painter.setPen(QPen(QColor("#2A3A52")))
        painter.drawRect(map_rect)

        scale_x = map_rect.width() / scene_rect.width()
        scale_y = map_rect.height() / scene_rect.height()
        scale = min(scale_x, scale_y)

        content_width = scene_rect.width() * scale
        content_height = scene_rect.height() * scale
        origin_x = map_rect.x() + (map_rect.width() - content_width) / 2.0
        origin_y = map_rect.y() + (map_rect.height() - content_height) / 2.0

        painter.fillRect(
            int(origin_x),
            int(origin_y),
            int(content_width),
            int(content_height),
            QColor("#172235"),
        )

        viewport_rect = self._viewport_rect(scene_rect, origin_x, origin_y, scale)
        painter.setPen(QPen(QColor("#0EA5FF"), 2))
        painter.setBrush(QBrush(QColor(14, 165, 255, 40)))
        painter.drawRect(viewport_rect)
        painter.end()
        super().paintEvent(event)

    def _scene_rect(self) -> QRectF:
        if self._canvas is None:
            return QRectF()
        return self._canvas.graphics_scene.sceneRect()

    def _viewport_rect(
        self,
        scene_rect: QRectF,
        origin_x: float,
        origin_y: float,
        scale: float,
    ) -> QRectF:
        if self._canvas is None:
            return QRectF(origin_x, origin_y, 20, 20)

        viewport = self._canvas.viewport().rect()
        top_left = self._canvas.mapToScene(viewport.topLeft())
        bottom_right = self._canvas.mapToScene(viewport.bottomRight())
        visible = QRectF(top_left, bottom_right).normalized()

        x = origin_x + (visible.left() - scene_rect.left()) * scale
        y = origin_y + (visible.top() - scene_rect.top()) * scale
        width = max(visible.width() * scale, 12.0)
        height = max(visible.height() * scale, 12.0)
        return QRectF(x, y, width, height)
