"""Device center view placeholder."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..widgets import CommercialCard


class DeviceCenterView(QWidget):
    """Placeholder for advanced device configuration."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("deviceCenterView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = CommercialCard("设备中心", self)
        label = QLabel("Motion / Spectrum / Camera / License / Plugin 配置占位区", card.body)
        label.setObjectName("commercialMutedLabel")
        label.setWordWrap(True)
        card.body_layout.addWidget(label, 1)
        layout.addWidget(card, 1)
