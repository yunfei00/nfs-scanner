"""Mini map widget for large realtime canvases."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from .realtime_canvas import RealtimeCanvas


class MiniMap(QWidget):
    """Small overview map with PCB thumbnail and green viewport frame."""

    MAP_WIDTH = 112
    MAP_HEIGHT = 84

    def __init__(self, canvas: RealtimeCanvas | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("nfsMiniMap")
        self._canvas = canvas
        self._board_image: QImage | None = None
        self.setFixedSize(self.MAP_WIDTH, self.MAP_HEIGHT)

    def bind_canvas(self, canvas: RealtimeCanvas) -> None:
        self._canvas = canvas
        canvas.viewport().installEventFilter(self)
        self.update()

    def set_board_image(self, image: QImage) -> None:
        self._board_image = image.copy()
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

        map_rect = self.rect().adjusted(4, 4, -4, -4)
        painter.setPen(QPen(QColor(42, 58, 82, 120)))
        painter.drawRect(map_rect)

        scale_x = map_rect.width() / scene_rect.width()
        scale_y = map_rect.height() / scene_rect.height()
        scale = min(scale_x, scale_y)

        content_width = scene_rect.width() * scale
        content_height = scene_rect.height() * scale
        origin_x = map_rect.x() + (map_rect.width() - content_width) / 2.0
        origin_y = map_rect.y() + (map_rect.height() - content_height) / 2.0
        content_rect = QRectF(origin_x, origin_y, content_width, content_height)

        if self._board_image is not None and not self._board_image.isNull():
            painter.drawImage(content_rect.toRect(), self._board_image)
        else:
            painter.fillRect(content_rect.toRect(), QColor("#1F4D38"))

        viewport_rect = self._viewport_rect(scene_rect, origin_x, origin_y, scale)
        painter.setPen(QPen(QColor("#22C55E"), 2))
        painter.setBrush(QBrush(QColor(34, 197, 94, 24)))
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
        width = max(visible.width() * scale, 10.0)
        height = max(visible.height() * scale, 10.0)
        return QRectF(x, y, width, height)


class MiniMapPanel(QFrame):
    """Compact minimap container with title label."""

    def __init__(self, canvas: RealtimeCanvas, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("nfsMiniMapPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)
        title = QLabel("全局视图", self)
        title.setObjectName("commercialMiniMapTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.map = MiniMap(canvas, self)
        layout.addWidget(title)
        layout.addWidget(self.map, 0, Qt.AlignmentFlag.AlignHCenter)

    def bind_canvas(self, canvas: RealtimeCanvas) -> None:
        self.map.bind_canvas(canvas)

    def set_board_image(self, image: QImage) -> None:
        self.map.set_board_image(image)

    def update(self) -> None:
        self.map.update()
        super().update()
