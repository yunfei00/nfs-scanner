"""Compact icon-style toolbar button for commercial UI."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton, QWidget

TOOL_BUTTON_WIDTH = 62
TOOL_BUTTON_HEIGHT = 48


class NFSIconToolButton(QToolButton):
    """Icon-first tool button with short caption and full-name tooltip."""

    clicked_action = Signal()

    def __init__(
        self,
        icon: QIcon | str,
        caption: str,
        *,
        full_caption: str = "",
        tooltip: str = "",
        primary: bool = False,
        danger: bool = False,
        success: bool = False,
        mock_disabled: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._full_caption = full_caption or caption
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
            self.setText(caption.replace("\n", ""))
        else:
            self.setText(f"{icon} {caption}")
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setToolTip(tooltip or self._full_caption)
        self.setProperty("fullCaption", self._full_caption)
        self.setAutoRaise(True)
        self.setIconSize(QSize(20, 20))
        font = self.font()
        font.setPixelSize(11)
        self.setFont(font)
        self.setFixedSize(TOOL_BUTTON_WIDTH, TOOL_BUTTON_HEIGHT)
        if mock_disabled:
            self.setProperty("mockDisabled", "true")
        self.clicked.connect(self.clicked_action.emit)

    def full_caption(self) -> str:
        """Return the full toolbar action name."""

        return self._full_caption
