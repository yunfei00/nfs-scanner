"""Offline data view placeholder."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..widgets import CommercialCard


class DataView(QWidget):
    """Placeholder for historical scan analysis."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dataView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = CommercialCard("数据视图", self)
        label = QLabel("历史任务列表与离线热力图分析占位区", card.body)
        label.setObjectName("commercialMutedLabel")
        label.setWordWrap(True)
        card.body_layout.addWidget(label, 1)
        layout.addWidget(card, 1)
