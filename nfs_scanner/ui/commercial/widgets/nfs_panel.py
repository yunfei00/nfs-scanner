"""Generic panel container for commercial UI regions."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget


class NFSPanel(QFrame):
    """Flat panel container without card title."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("nfsPanel")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(8)
