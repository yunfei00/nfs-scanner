"""Status bar placeholder for the commercial UI."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CommercialStatusBar(QWidget):
    """Placeholder status bar. Expanded in Sprint 001 Task 03."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialStatusBar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.addWidget(QLabel("Status Bar (placeholder)", self))
