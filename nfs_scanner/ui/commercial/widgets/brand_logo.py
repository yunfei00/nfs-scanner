"""Painted NFS brand logo block for the commercial top header."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class NFSBrandLogoFrame(QFrame):
    """Blue gradient logo tile with inner highlight — no external image assets."""

    LOGO_SIZE = 42

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialTitleBarLogo")
        self.setProperty("brandBlueBlock", True)
        self.setProperty("brandLogoBlue", True)
        self.setFixedSize(self.LOGO_SIZE, self.LOGO_SIZE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        logo_text = QLabel("NFS", self)
        logo_text.setObjectName("commercialTitleBarLogoText")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(logo_text)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(0, 0, -1, -1)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0.0, QColor("#0EA5FF"))
        gradient.setColorAt(0.45, QColor("#0284C7"))
        gradient.setColorAt(1.0, QColor("#1D4ED8"))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#7DD3FC"), 1))
        painter.drawRoundedRect(rect, 8, 8)

        inset = rect.adjusted(3, 3, -3, -3)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 70), 1))
        painter.drawRoundedRect(inset, 6, 6)

        accent = rect.adjusted(8, 8, -8, -8)
        painter.setPen(QPen(QColor(255, 255, 255, 35), 1))
        painter.drawRoundedRect(accent, 4, 4)

        painter.end()
        super().paintEvent(event)
