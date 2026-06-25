"""Real-time workspace view placeholder."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from ..widgets import CommercialCard


class RealtimeView(QWidget):
    """Placeholder for the live scanning canvas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("realtimeView")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        card = CommercialCard("实时视图", self)
        canvas_placeholder = QFrame(card.body)
        canvas_placeholder.setObjectName("realtimeCanvasPlaceholder")
        canvas_placeholder.setMinimumHeight(320)
        canvas_layout = QVBoxLayout(canvas_placeholder)
        canvas_layout.setContentsMargins(12, 12, 12, 12)
        label = QLabel("QGraphicsView 画布占位区（Photo / Heatmap / Path / Marker）", canvas_placeholder)
        label.setObjectName("commercialMutedLabel")
        label.setWordWrap(True)
        canvas_layout.addStretch(1)
        canvas_layout.addWidget(label)
        canvas_layout.addStretch(1)
        card.body_layout.addWidget(canvas_placeholder, 1)
        layout.addWidget(card, 1)
