"""Top toolbar placeholder for the commercial UI."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from .widgets import CommercialCard


class CommercialToolbar(QWidget):
    """Placeholder top toolbar with themed action buttons."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialToolbar")
        self.setMinimumHeight(64)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        brand_card = CommercialCard("近场扫描系统", self)
        brand_card.body_layout.addWidget(
            self._create_muted_label("Near Field Scanner v0.1", brand_card.body)
        )
        layout.addWidget(brand_card)

        for text, object_name in (
            ("新建项目", "secondaryButton"),
            ("打开项目", "secondaryButton"),
            ("保存项目", "secondaryButton"),
            ("连接设备", "secondaryButton"),
            ("开始扫描", "primaryButton"),
            ("停止扫描", "dangerButton"),
        ):
            button = QPushButton(text, self)
            button.setObjectName(object_name)
            layout.addWidget(button)

        layout.addStretch(1)

    def _create_muted_label(self, text: str, parent: QWidget):
        from PySide6.QtWidgets import QLabel

        label = QLabel(text, parent)
        label.setObjectName("commercialMutedLabel")
        return label
