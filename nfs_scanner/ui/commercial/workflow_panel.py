"""Left workflow panel placeholder for the commercial UI."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CommercialWorkflowPanel(QWidget):
    """Placeholder workflow panel. Expanded in Sprint 001 Task 04."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialWorkflowPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(QLabel("Workflow (placeholder)", self))
