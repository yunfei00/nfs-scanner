"""Scene layer definitions and base layer behavior."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene


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
        self._items.append(item)
        return item

    @abstractmethod
    def build_mock(self) -> None:
        """Populate the layer with mock content."""


class PhotoLayer(BaseLayer):
    """Photo layer. Expanded in Task 04."""

    kind = LayerKind.PHOTO

    def build_mock(self) -> None:
        return


class HeatmapLayer(BaseLayer):
    """Heatmap layer. Expanded in Task 05."""

    kind = LayerKind.HEATMAP

    def build_mock(self) -> None:
        return


class ScanPathLayer(BaseLayer):
    """Scan path layer. Expanded in Task 06."""

    kind = LayerKind.PATH

    def build_mock(self) -> None:
        return


class MarkerLayer(BaseLayer):
    """Marker layer. Expanded in Task 07."""

    kind = LayerKind.MARKER

    def build_mock(self) -> None:
        return


class AnnotationLayer(BaseLayer):
    """Annotation layer placeholder."""

    kind = LayerKind.ANNOTATION

    def build_mock(self) -> None:
        return
