"""Base realtime canvas with zoom, pan, fit, and reset."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QWheelEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget


class RealtimeCanvas(QGraphicsView):
    """QGraphicsView-based canvas for aligned realtime layers."""

    MIN_ZOOM = 0.1
    MAX_ZOOM = 8.0
    ZOOM_FACTOR = 1.15

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("realtimeCanvas")
        self._scene = QGraphicsScene(self)
        self._zoom_level = 1.0
        self._is_panning = False
        self._setup_view()

    @property
    def graphics_scene(self) -> QGraphicsScene:
        """Return the owned graphics scene."""

        return self._scene

    def _setup_view(self) -> None:
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setBackgroundBrush(QBrush(QColor("#0B1220")))
        self._show_empty_state()

    def _show_empty_state(self) -> None:
        """Reserve a stable scene rect before layers are attached."""

        self._scene.setSceneRect(0, 0, 800, 600)

    def set_scene_rect(self, x: float, y: float, width: float, height: float) -> None:
        """Update the logical scene bounds shared by all layers."""

        self._scene.setSceneRect(x, y, width, height)

    def fit_view(self) -> None:
        """Fit the entire scene rect into the viewport."""

        scene_rect = self._scene.sceneRect()
        if scene_rect.isEmpty():
            return
        self.resetTransform()
        self._zoom_level = 1.0
        self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)

    def reset_view(self) -> None:
        """Reset transform and center on the scene."""

        self.resetTransform()
        self._zoom_level = 1.0
        self.centerOn(self._scene.sceneRect().center())

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom in or out around the cursor."""

        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return

        factor = self.ZOOM_FACTOR if delta > 0 else 1.0 / self.ZOOM_FACTOR
        next_zoom = self._zoom_level * factor
        if next_zoom < self.MIN_ZOOM or next_zoom > self.MAX_ZOOM:
            event.accept()
            return

        self._zoom_level = next_zoom
        self.scale(factor, factor)
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        super().mouseReleaseEvent(event)
