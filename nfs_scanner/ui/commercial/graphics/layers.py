"""Scene layer definitions and base layer behavior."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from enum import Enum

from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage, QPolygonF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem, QGraphicsScene

from .mock_assets import CANVAS_HEIGHT, CANVAS_WIDTH, create_mock_board_qimage


def _direction_arrow_polygon(tip: QPointF, direction: QPointF, *, size: float = 8.0) -> QPolygonF:
    """Build a small arrow head aligned with one path segment direction."""

    length = math.hypot(direction.x(), direction.y())
    if length == 0:
        return QPolygonF()

    unit_x = direction.x() / length
    unit_y = direction.y() / length
    base = QPointF(tip.x() - unit_x * size, tip.y() - unit_y * size)
    offset_x = -unit_y * size * 0.5
    offset_y = unit_x * size * 0.5
    return QPolygonF(
        [
            tip,
            QPointF(base.x() + offset_x, base.y() + offset_y),
            QPointF(base.x() - offset_x, base.y() - offset_y),
        ]
    )


class LayerKind(str, Enum):
    """Stable layer identifiers."""

    PHOTO = "photo"
    HEATMAP = "heatmap"
    PATH = "path"
    MARKER = "marker"
    ANNOTATION = "annotation"


class BaseLayer(ABC):
    """Shared layer contract for all canvas overlays."""

    kind: LayerKind

    def __init__(self, scene: QGraphicsScene) -> None:
        self._scene = scene
        self._items: list[QGraphicsItem] = []
        self._z_value = 0.0

    @property
    def z_value(self) -> float:
        """Stable scene z-order assigned by LayerManager."""

        return self._z_value

    def set_z_value(self, z_value: float) -> None:
        """Assign layer z-order and apply it to existing items."""

        self._z_value = float(z_value)
        for item in self._items:
            item.setZValue(self._z_value)

    def items(self) -> list[QGraphicsItem]:
        """Return graphics items owned by this layer."""

        return list(self._items)

    def set_visible(self, visible: bool) -> None:
        """Toggle visibility for all items in this layer."""

        for item in self._items:
            item.setVisible(visible)

    def clear(self) -> None:
        """Remove all items from the scene."""

        for item in self._items:
            self._scene.removeItem(item)
        self._items.clear()

    def _register_item(self, item: QGraphicsItem) -> QGraphicsItem:
        self._scene.addItem(item)
        item.setZValue(self._z_value)
        self._items.append(item)
        return item

    @abstractmethod
    def build_mock(self) -> None:
        """Populate the layer with mock content."""


class PhotoLayer(BaseLayer):
    """Display camera photos, imported images, or mock board backgrounds."""

    kind = LayerKind.PHOTO

    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self._pixmap_item: QGraphicsPixmapItem | None = None

    def build_mock(self) -> None:
        """Show a generated mock board image."""

        self.set_photo_image(create_mock_board_qimage())

    def set_photo_image(self, image: QImage) -> None:
        """Load one photo image into the layer (future camera/import API)."""

        from PySide6.QtGui import QPixmap

        self.clear()
        pixmap = QPixmap.fromImage(image)
        item = QGraphicsPixmapItem(pixmap)
        item.setPos(0, 0)
        self._pixmap_item = self._register_item(item)

    @property
    def canvas_width(self) -> int:
        if self._pixmap_item is not None:
            return int(self._pixmap_item.pixmap().width())
        return CANVAS_WIDTH

    @property
    def canvas_height(self) -> int:
        if self._pixmap_item is not None:
            return int(self._pixmap_item.pixmap().height())
        return CANVAS_HEIGHT


class HeatmapLayer(BaseLayer):
    """Display one heatmap image overlay aligned to the photo layer."""

    kind = LayerKind.HEATMAP

    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._opacity = 0.65
        self._lut_name = "viridis"

    def build_mock(self) -> None:
        from .mock_assets import create_mock_heatmap_qimage

        self.set_heatmap_image(create_mock_heatmap_qimage())

    def set_heatmap_image(self, image: QImage) -> None:
        """Load one heatmap image as a single pixmap layer."""

        from PySide6.QtGui import QPixmap

        self.clear()
        pixmap = QPixmap.fromImage(image)
        item = QGraphicsPixmapItem(pixmap)
        item.setPos(0, 0)
        item.setOpacity(self._opacity)
        self._pixmap_item = self._register_item(item)

    def set_opacity(self, opacity: float) -> None:
        """Update heatmap overlay opacity (0.0 to 1.0)."""

        self._opacity = max(0.0, min(float(opacity), 1.0))
        if self._pixmap_item is not None:
            self._pixmap_item.setOpacity(self._opacity)

    def set_lut_name(self, lut_name: str) -> None:
        """Placeholder LUT selector for future visualization settings."""

        self._lut_name = lut_name.strip() or "viridis"

    @property
    def lut_name(self) -> str:
        return self._lut_name


class ScanPathLayer(BaseLayer):
    """Display mock snake scan paths, points, and direction hints."""

    kind = LayerKind.PATH

    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self._points: list[tuple[float, float]] = []
        self._current_index = 0
        self._completed_count = 0

    def build_mock(self) -> None:
        from .mock_assets import generate_snake_path_points

        self.set_path_points(generate_snake_path_points())
        self.set_progress(current_index=3, completed_count=2)

    def set_path_points(self, points: list[tuple[float, float]]) -> None:
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtGui import QBrush, QColor, QPainterPath, QPen, QPolygonF
        from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsPolygonItem

        from .path_display_policy import (
            path_line_width,
            resolve_display_level,
            select_arrow_segment_indices,
            select_dot_indices,
        )

        self.clear()
        self._points = list(points)
        if len(self._points) < 2:
            return

        display_level = resolve_display_level(len(self._points))
        line_width = path_line_width(display_level)

        path = QPainterPath(QPointF(*self._points[0]))
        for x_value, y_value in self._points[1:]:
            path.lineTo(x_value, y_value)

        path_item = QGraphicsPathItem(path)
        path_item.setPen(QPen(QColor("#06D6E8"), line_width))
        self._register_item(path_item)

        dot_radius = 3.0 if display_level.value == "full" else 2.5
        for index in select_arrow_segment_indices(len(self._points), display_level):
            start = QPointF(*self._points[index])
            end = QPointF(*self._points[index + 1])
            arrow = _direction_arrow_polygon(end, end - start, size=7.0 if display_level.value == "full" else 6.0)
            if arrow.isEmpty():
                continue
            arrow_item = QGraphicsPolygonItem(arrow)
            arrow_item.setBrush(QBrush(QColor("#0EA5FF")))
            arrow_item.setPen(QPen(Qt.PenStyle.NoPen))
            self._register_item(arrow_item)

        for index in select_dot_indices(len(self._points), display_level):
            x_value, y_value = self._points[index]
            dot = QGraphicsEllipseItem(
                x_value - dot_radius,
                y_value - dot_radius,
                dot_radius * 2,
                dot_radius * 2,
            )
            dot.setBrush(QBrush(QColor("#E8EEF8")))
            dot.setPen(QPen(QColor("#2A3A52")))
            self._register_item(dot)

    def set_progress(self, *, current_index: int, completed_count: int) -> None:
        """Reserve scan progress state for future runtime integration."""

        self._current_index = max(0, current_index)
        self._completed_count = max(0, completed_count)


class MarkerLayer(BaseLayer):
    """Display mock markers with tooltip metadata."""

    kind = LayerKind.MARKER

    def build_mock(self) -> None:
        from .marker_items import MarkerData, MarkerItem
        from .mock_assets import board_content_rect

        self.clear()
        board_x, board_y, board_w, board_h = board_content_rect()
        marker = MarkerItem(
            MarkerData(
                x=board_x + board_w * 0.55,
                y=board_y + board_h * 0.42,
                z=5.0,
                frequency="1.00 GHz",
                amplitude="-41.2 dBm",
            )
        )
        self._register_item(marker)

    def add_marker(self, data) -> "MarkerItem":
        from .marker_items import MarkerItem

        marker = MarkerItem(data)
        self._register_item(marker)
        return marker


class AnnotationLayer(BaseLayer):
    """Annotation layer placeholder."""

    kind = LayerKind.ANNOTATION

    def build_mock(self) -> None:
        return
