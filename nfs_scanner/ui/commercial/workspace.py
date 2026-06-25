"""Central workspace placeholder for the commercial UI."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .widgets import CommercialCard


class CommercialWorkspace(QWidget):
    """Placeholder workspace region. Expanded in Sprint 001 Task 05."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialWorkspace")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        card = CommercialCard("中央工作区", self)
        placeholder = QLabel("Workspace placeholder — tabs arrive in Task 05", card.body)
        placeholder.setObjectName("commercialMutedLabel")
        card.body_layout.addWidget(placeholder, 1)
        layout.addWidget(card, 1)
