"""Target-style brand block for the commercial top header."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from nfs_scanner.version import APP_VERSION


class CommercialBrandArea(QWidget):
    """Logo square + hierarchical product title block matching the target header."""

    BRAND_WIDTH = 210

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
        root.setContentsMargins(0, 0, 8, 0)
        root.setSpacing(8)

        self._logo_block = QFrame(self)
        self._logo_block.setObjectName("commercialTitleBarLogo")
        self._logo_block.setFixedSize(42, 42)
        logo_layout = QVBoxLayout(self._logo_block)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_text = QLabel("NFS", self._logo_block)
        logo_text.setObjectName("commercialTitleBarLogoText")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_text)

        text_column = QWidget(self)
        text_column.setObjectName("commercialBrandTextColumn")
        text_layout = QVBoxLayout(text_column)
        text_layout.setContentsMargins(0, 2, 0, 2)
        text_layout.setSpacing(2)

        self._title_label = QLabel("近场扫描系统", text_column)
        self._title_label.setObjectName("commercialTitleBarTitle")

        subtitle_row = QWidget(text_column)
        subtitle_layout = QHBoxLayout(subtitle_row)
        subtitle_layout.setContentsMargins(0, 0, 0, 0)
        subtitle_layout.setSpacing(6)

        self._subtitle_label = QLabel("Near Field Scanner", subtitle_row)
        self._subtitle_label.setObjectName("commercialTitleBarSubtitle")

        self._version_badge = QLabel(f"v{APP_VERSION}", subtitle_row)
        self._version_badge.setObjectName("commercialTitleBarBadge")
        self._version_badge.setToolTip("Mock · Dry Run · 无硬件控制")

        subtitle_layout.addWidget(self._subtitle_label, 0)
        subtitle_layout.addWidget(self._version_badge, 0)
        subtitle_layout.addStretch(1)

        text_layout.addWidget(self._title_label)
        text_layout.addWidget(subtitle_row)

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
