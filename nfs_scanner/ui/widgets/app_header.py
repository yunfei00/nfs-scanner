"""Header for the unified NFS Scanner main window."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from nfs_scanner.version import APP_NAME, APP_VERSION


class ApplicationHeader(QFrame):
    """Compact product identity and runtime-safety header."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("applicationHeader")
        self.setFixedHeight(68)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(16)

        brand = QVBoxLayout()
        brand.setSpacing(1)
        title = QLabel(f"{APP_NAME}  <span style='color:#718096'>v{APP_VERSION}</span>", self)
        title.setObjectName("applicationTitle")
        subtitle = QLabel("近场扫描与射频测量工作台", self)
        subtitle.setObjectName("applicationSubtitle")
        brand.addWidget(title)
        brand.addWidget(subtitle)

        baseline_badge = QLabel("统一控制台", self)
        baseline_badge.setObjectName("baselineBadge")
        safety_badge = QLabel("设备操作需显式连接", self)
        safety_badge.setObjectName("safetyBadge")

        layout.addLayout(brand)
        layout.addStretch(1)
        layout.addWidget(baseline_badge)
        layout.addWidget(safety_badge)
