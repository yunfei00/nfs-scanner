"""Color bar placeholder."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget


class ColorBar(QWidget):
    """LUT color bar placeholder. Expanded in Sprint 002 Task 08."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialColorBar")
        QLabel("ColorBar", self)
