"""Top toolbar for the commercial UI shell."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class CommercialToolbar(QWidget):
    """Top toolbar with brand area and primary action placeholders."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialToolbar")
        self.setMinimumHeight(64)
        self.setMaximumHeight(64)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        brand = QWidget(self)
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(8)

        title = QLabel("近场扫描系统", brand)
        title.setObjectName("commercialSectionTitle")
        subtitle = QLabel("Near Field Scanner", brand)
        subtitle.setObjectName("commercialMutedLabel")
        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)
        layout.addWidget(brand)

        for text, object_name in (
            ("新建", "secondaryButton"),
            ("打开", "secondaryButton"),
            ("保存", "secondaryButton"),
            ("连接设备", "secondaryButton"),
            ("开始扫描", "primaryButton"),
            ("停止", "dangerButton"),
        ):
            button = QPushButton(text, self)
            button.setObjectName(object_name)
            layout.addWidget(button)

        layout.addStretch(1)

        license_label = QLabel("Trial License", self)
        license_label.setObjectName("commercialMutedLabel")
        layout.addWidget(license_label)
