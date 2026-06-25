"""Bottom dock placeholder for the commercial UI."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CommercialBottomDock(QWidget):
    """Placeholder bottom dock. Expanded in Sprint 001 Task 06."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialBottomDock")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(QLabel("Bottom Dock (placeholder)", self))
