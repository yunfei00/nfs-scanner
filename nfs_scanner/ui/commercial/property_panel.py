"""Right property panel placeholder for the commercial UI."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CommercialPropertyPanel(QWidget):
    """Placeholder property panel. Expanded in Sprint 001 Task 06."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialPropertyPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(QLabel("Property Panel (placeholder)", self))
