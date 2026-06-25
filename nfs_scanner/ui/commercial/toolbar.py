"""Top toolbar placeholder for the commercial UI."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CommercialToolbar(QWidget):
    """Placeholder top toolbar. Expanded in Sprint 001 Task 03."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialToolbar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(QLabel("Toolbar (placeholder)", self))
