"""Report center view placeholder."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..widgets import CommercialCard


class ReportView(QWidget):
    """Placeholder for report generation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("reportView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = CommercialCard("报告中心", self)
        label = QLabel("模板化 PDF 报告生成占位区", card.body)
        label.setObjectName("commercialMutedLabel")
        label.setWordWrap(True)
        card.body_layout.addWidget(label, 1)
        layout.addWidget(card, 1)
