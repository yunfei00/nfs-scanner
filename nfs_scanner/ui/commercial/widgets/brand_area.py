"""Target-style brand block for the commercial top header."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from nfs_scanner.version import APP_VERSION


class CommercialBrandArea(QWidget):
    """Logo square + hierarchical product title block matching the target header."""

    BRAND_WIDTH = 248

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialBrandArea")
        self.setFixedWidth(self.BRAND_WIDTH)
        self._logo_block: QFrame | None = None
        self._title_label: QLabel | None = None
        self._subtitle_label: QLabel | None = None
        self._version_badge: QLabel | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 10, 0)
        root.setSpacing(10)

        self._logo_block = QFrame(self)
        self._logo_block.setObjectName("commercialTitleBarLogo")
        self._logo_block.setFixedSize(44, 44)
        self._logo_block.setStyleSheet(
            "QFrame#commercialTitleBarLogo {"
            "background-color: #0EA5FF;"
            "border: 1px solid #54C8FF;"
            "border-radius: 8px;"
            "}"
        )
        logo_layout = QVBoxLayout(self._logo_block)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(0)
        logo_text = QLabel("NFS", self._logo_block)
        logo_text.setObjectName("commercialTitleBarLogoText")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_text.setStyleSheet(
            "QLabel#commercialTitleBarLogoText {"
            "background-color: transparent;"
            "color: #04111F;"
            "font-size: 15px;"
            "font-weight: 800;"
            "letter-spacing: 1px;"
            "}"
        )
        logo_layout.addWidget(logo_text)

        text_column = QWidget(self)
        text_column.setObjectName("commercialBrandTextColumn")
        text_layout = QVBoxLayout(text_column)
        text_layout.setContentsMargins(0, 1, 0, 1)
        text_layout.setSpacing(1)

        title_row = QWidget(text_column)
        title_row.setObjectName("commercialBrandTitleRow")
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)

        self._title_label = QLabel("近场扫描系统", title_row)
        self._title_label.setObjectName("commercialTitleBarTitle")
        self._title_label.setStyleSheet(
            "QLabel#commercialTitleBarTitle {"
            "background-color: transparent;"
            "color: #F4F8FF;"
            "font-size: 16px;"
            "font-weight: 700;"
            "}"
        )

        self._version_badge = QLabel(f"v{APP_VERSION}", title_row)
        self._version_badge.setObjectName("commercialTitleBarBadge")
        self._version_badge.setToolTip("Mock · Dry Run · 无硬件控制")
        self._version_badge.setStyleSheet(
            "QLabel#commercialTitleBarBadge {"
            "background-color: rgba(14, 165, 255, 0.16);"
            "border: 1px solid rgba(84, 200, 255, 0.50);"
            "border-radius: 5px;"
            "color: #8FDBFF;"
            "font-size: 10px;"
            "font-weight: 700;"
            "padding: 1px 6px;"
            "}"
        )

        title_layout.addWidget(self._title_label, 0, Qt.AlignmentFlag.AlignVCenter)
        title_layout.addWidget(self._version_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        title_layout.addStretch(1)

        self._subtitle_label = QLabel("Near Field Scanner · Commercial Demo", text_column)
        self._subtitle_label.setObjectName("commercialTitleBarSubtitle")
        self._subtitle_label.setStyleSheet(
            "QLabel#commercialTitleBarSubtitle {"
            "background-color: transparent;"
            "color: #8FA0B8;"
            "font-size: 10px;"
            "font-weight: 500;"
            "letter-spacing: 0.5px;"
            "}"
        )

        text_layout.addWidget(title_row)
        text_layout.addWidget(self._subtitle_label)

        root.addWidget(self._logo_block, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(text_column, 1, Qt.AlignmentFlag.AlignVCenter)

    def logo_block(self) -> QFrame | None:
        return self._logo_block

    def _label_top_y_in(self, label: QLabel, ancestor: QWidget) -> int:
        """Map a label's top edge into *ancestor* coordinates."""

        return label.mapTo(ancestor, label.rect().topLeft()).y()

    def has_title_hierarchy(self) -> bool:
        """Return True when Chinese title sits above English subtitle."""

        if self._title_label is None or self._subtitle_label is None or self._logo_block is None:
            return False
        title_y = self._label_top_y_in(self._title_label, self)
        subtitle_y = self._label_top_y_in(self._subtitle_label, self)
        title_above_subtitle = title_y < subtitle_y - 4
        logo_large_enough = self._logo_block.width() >= 40 and self._logo_block.height() >= 40
        badge_present = self._version_badge is not None and self._version_badge.text().startswith("v")
        return title_above_subtitle and logo_large_enough and badge_present

    def is_flat_text_row(self) -> bool:
        """Return True when title and subtitle share the same baseline (undesired)."""

        if self._title_label is None or self._subtitle_label is None:
            return True
        title_y = self._label_top_y_in(self._title_label, self)
        subtitle_y = self._label_top_y_in(self._subtitle_label, self)
        return abs(title_y - subtitle_y) <= 2
