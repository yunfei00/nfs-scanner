"""3D surface view placeholder."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..widgets import CommercialCard


class ThreeDView(QWidget):
    """Placeholder for the 3D surface visualization."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("threeDView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = CommercialCard("3D 视图", self)
        label = QLabel("XY 网格 Surface 占位区（旋转 / 平移 / 缩放）", card.body)
        label.setObjectName("commercialMutedLabel")
        label.setWordWrap(True)
        card.body_layout.addWidget(label, 1)
        layout.addWidget(card, 1)
