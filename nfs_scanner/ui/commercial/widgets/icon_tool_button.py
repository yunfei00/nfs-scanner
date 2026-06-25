"""Compact icon-style toolbar button for commercial UI."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QToolButton, QWidget


class NFSIconToolButton(QToolButton):
    """Icon-first tool button with optional caption for instrument-style toolbar."""

    clicked_action = Signal()

    def __init__(
        self,
        icon_text: str,
        caption: str,
        *,
        tooltip: str = "",
        primary: bool = False,
        danger: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(
            "commercialIconToolDanger"
            if danger
            else ("commercialIconToolPrimary" if primary else "commercialIconToolButton")
        )
        self.setText(f"{icon_text}\n{caption}")
        self.setToolTip(tooltip or caption)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setAutoRaise(True)
        self.setFixedSize(52, 46)
        self.clicked.connect(self.clicked_action.emit)
