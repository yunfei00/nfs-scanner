"""Target-style brand block for the commercial top header."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from nfs_scanner.version import APP_VERSION

from .brand_logo import NFSBrandLogoFrame


class CommercialBrandArea(QWidget):
    """Logo square + hierarchical product title block matching the target header."""

    BRAND_WIDTH = 220

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialBrandArea")
        self.setFixedWidth(self.BRAND_WIDTH)
        self._logo_block: NFSBrandLogoFrame | None = None
        self._title_label: QLabel | None = None
        self._subtitle_label: QLabel | None = None
        self._version_badge: QLabel | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 6, 0)
        root.setSpacing(8)

        self._logo_block = NFSBrandLogoFrame(self)

        text_column = QWidget(self)
        text_column.setObjectName("commercialBrandTextColumn")
        text_layout = QVBoxLayout(text_column)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)

        title_row = QWidget(text_column)
        title_row.setObjectName("commercialBrandTitleRow")
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        self._title_label = QLabel("近场扫描系统", title_row)
        self._title_label.setObjectName("commercialTitleBarTitle")

        self._version_badge = QLabel(f"v{APP_VERSION}", title_row)
        self._version_badge.setObjectName("commercialTitleBarBadge")
        self._version_badge.setToolTip("Mock · Dry Run · 无硬件控制")

        title_layout.addWidget(self._title_label, 0, Qt.AlignmentFlag.AlignVCenter)
        title_layout.addStretch(1)
        title_layout.addWidget(self._version_badge, 0, Qt.AlignmentFlag.AlignVCenter)

        self._subtitle_label = QLabel("Near Field Scanner", text_column)
        self._subtitle_label.setObjectName("commercialTitleBarSubtitle")

        text_layout.addWidget(title_row)
        text_layout.addWidget(self._subtitle_label)

        root.addWidget(self._logo_block, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(text_column, 1, Qt.AlignmentFlag.AlignVCenter)

    def logo_block(self) -> NFSBrandLogoFrame | None:
        return self._logo_block

    def version_badge(self) -> QLabel | None:
        return self._version_badge

    def _label_top_y_in(self, label: QLabel, ancestor: QWidget) -> int:
        return label.mapTo(ancestor, label.rect().topLeft()).y()

    def has_title_hierarchy(self) -> bool:
        if self._title_label is None or self._subtitle_label is None or self._logo_block is None:
            return False
        title_y = self._label_top_y_in(self._title_label, self)
        subtitle_y = self._label_top_y_in(self._subtitle_label, self)
        title_above_subtitle = title_y < subtitle_y - 4
        logo_large_enough = self._logo_block.width() >= 40 and self._logo_block.height() >= 40
        badge_present = self._version_badge is not None and self._version_badge.text().startswith("v")
        return title_above_subtitle and logo_large_enough and badge_present

    def is_flat_text_row(self) -> bool:
        if self._title_label is None or self._subtitle_label is None:
            return True
        title_y = self._label_top_y_in(self._title_label, self)
        subtitle_y = self._label_top_y_in(self._subtitle_label, self)
        return abs(title_y - subtitle_y) <= 2
