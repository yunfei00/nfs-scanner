"""Compact icon-style toolbar button for commercial UI."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton, QWidget


def _toolbar_caption_lines(caption: str) -> str:
    """Return the full one-line toolbar caption."""

    return caption.replace("\n", "")


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
            self.setText(f"{icon} {caption}")
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        if isinstance(icon, QIcon):
            self.setText(_toolbar_caption_lines(caption))
        self.setToolTip(tooltip or caption)
        self.setAutoRaise(True)
        self.setIconSize(QSize(16, 16))
        font = self.font()
        font.setPixelSize(10)
        self.setFont(font)
        self.setFixedSize(68, 48)
        self.clicked.connect(self.clicked_action.emit)
