"""Bottom dock placeholder for the commercial UI."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .widgets import CommercialCard


class CommercialBottomDock(QWidget):
    """Placeholder bottom dock. Expanded in Sprint 001 Task 06."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialBottomDock")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        card = CommercialCard("底部 Dock", self)
        placeholder = QLabel("Spectrum / Statistics / Logs arrive in Task 06", card.body)
        placeholder.setObjectName("commercialMutedLabel")
        card.body_layout.addWidget(placeholder, 1)
        layout.addWidget(card, 1)
