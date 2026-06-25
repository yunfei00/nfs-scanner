"""Layer ordering manager placeholder."""

from __future__ import annotations

from PySide6.QtWidgets import QGraphicsScene


class LayerManager:
    """Manage commercial canvas layers. Expanded in Sprint 002 Task 03."""

    def __init__(self, scene: QGraphicsScene) -> None:
        self._scene = scene
