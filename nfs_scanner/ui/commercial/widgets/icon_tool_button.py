"""Compact icon-style toolbar button for commercial UI."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton, QWidget


def _toolbar_caption_lines(caption: str) -> str:
    """Split a short Chinese caption into two lines for compact toolbar buttons."""

    if "\n" in caption or len(caption) <= 2:
        return caption
    if len(caption) in (3, 4):
        return f"{caption[:2]}\n{caption[2:]}"
    midpoint = len(caption) // 2
    return f"{caption[:midpoint]}\n{caption[midpoint:]}"


class NFSIconToolButton(QToolButton):
    """Icon-first tool button with caption for instrument-style toolbar."""

    clicked_action = Signal()

    def __init__(
        self,
        icon: QIcon | str,
        caption: str,
        *,
        tooltip: str = "",
        primary: bool = False,
        danger: bool = False,
        success: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(
            "commercialIconToolDanger"
            if danger
            else (
                "commercialIconToolSuccess"
                if success
                else ("commercialIconToolPrimary" if primary else "commercialIconToolButton")
            )
        )
        if isinstance(icon, QIcon):
            self.setIcon(icon)
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        else:
            self.setText(f"{icon}\n{caption}")
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        if isinstance(icon, QIcon):
            self.setText(_toolbar_caption_lines(caption))
        self.setToolTip(tooltip or caption)
        self.setAutoRaise(True)
        self.setIconSize(QSize(20, 20))
        font = self.font()
        font.setPixelSize(11)
        self.setFont(font)
        self.setFixedSize(52, 48)
        self.clicked.connect(self.clicked_action.emit)
