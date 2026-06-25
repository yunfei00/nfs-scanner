"""Demo mode indicator banner for commercial UI."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from nfs_scanner.core.integration_safety import REAL_DEVICE_ENABLED


class DemoModeBanner(QFrame):
    """Shows mock / dry-run / no-hardware status and optional reset."""

    reset_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("demoModeBanner")
        self.setMaximumHeight(32)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(12)

        badges = ("MOCK", "DRY RUN", "NO HARDWARE CONTROL")
        for text in badges:
            label = QLabel(text, self)
            label.setObjectName("demoModeBadge")
            layout.addWidget(label)

        real_label = QLabel(
            "REAL DEVICE ENABLED" if REAL_DEVICE_ENABLED else "REAL DEVICE DISABLED",
            self,
        )
        real_label.setObjectName("demoModeRealBadge")
        layout.addWidget(real_label)

        layout.addStretch(1)

        reset_button = QPushButton("重置 Demo", self)
        reset_button.setObjectName("demoResetButton")
        reset_button.clicked.connect(self.reset_requested.emit)
        layout.addWidget(reset_button)
