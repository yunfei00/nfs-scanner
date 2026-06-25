"""Right property panel placeholder for the commercial UI."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from .widgets import CommercialCard


class CommercialPropertyPanel(QScrollArea):
    """Placeholder property panel. Expanded in Sprint 001 Task 06."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialPropertyPanel")
        self.setWidgetResizable(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        card = CommercialCard("属性面板", container)
        placeholder = QLabel("Property tabs arrive in Task 06", card.body)
        placeholder.setObjectName("commercialMutedLabel")
        card.body_layout.addWidget(placeholder)
        layout.addWidget(card)
        layout.addStretch(1)
        self.setWidget(container)
