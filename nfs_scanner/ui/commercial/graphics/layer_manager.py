"""Layer ordering manager for the commercial realtime canvas."""

from __future__ import annotations

from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene

from .layers import AnnotationLayer, BaseLayer, HeatmapLayer, LayerKind, MarkerLayer, PhotoLayer, ScanPathLayer

_LAYER_ORDER: tuple[LayerKind, ...] = (
    LayerKind.PHOTO,
    LayerKind.HEATMAP,
    LayerKind.PATH,
    LayerKind.MARKER,
    LayerKind.ANNOTATION,
)

_LAYER_TYPES: dict[LayerKind, type[BaseLayer]] = {
    LayerKind.PHOTO: PhotoLayer,
    LayerKind.HEATMAP: HeatmapLayer,
    LayerKind.PATH: ScanPathLayer,
    LayerKind.MARKER: MarkerLayer,
    LayerKind.ANNOTATION: AnnotationLayer,
}


class LayerManager:
    """Manage layer creation, visibility, ordering, and cleanup."""

    def __init__(self, scene: QGraphicsScene) -> None:
        self._scene = scene
        self._layers: dict[LayerKind, BaseLayer] = {}

    def ensure_layer(self, kind: LayerKind) -> BaseLayer:
        """Return an existing layer or create one in stable order."""

        layer = self._layers.get(kind)
        if layer is not None:
            return layer

        layer_type = _LAYER_TYPES[kind]
        layer = layer_type(self._scene)
        self._layers[kind] = layer
        self._apply_z_order()
        return layer

    def get_layer(self, kind: LayerKind) -> BaseLayer | None:
        """Return one layer if it exists."""

        return self._layers.get(kind)

    def set_layer_visible(self, kind: LayerKind, visible: bool) -> None:
        """Show or hide one layer."""

        layer = self._layers.get(kind)
        if layer is not None:
            layer.set_visible(visible)

    def clear_layer(self, kind: LayerKind) -> None:
        """Clear one layer contents without removing it from the manager."""

        layer = self._layers.get(kind)
        if layer is not None:
            layer.clear()

    def clear_all(self) -> None:
        """Clear every managed layer."""

        for layer in self._layers.values():
            layer.clear()

    def layer_kinds(self) -> tuple[LayerKind, ...]:
        """Return currently registered layers in stable order."""

        return tuple(kind for kind in _LAYER_ORDER if kind in self._layers)

    def _apply_z_order(self) -> None:
        for index, kind in enumerate(_LAYER_ORDER):
            layer = self._layers.get(kind)
            if layer is None:
                continue
            for item in layer.items():
                item.setZValue(float(index))
