"""Mini map placeholder."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget


class MiniMap(QWidget):
    """Viewport mini map placeholder. Expanded in Sprint 002 Task 08."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialMiniMap")
        QLabel("MiniMap", self)
