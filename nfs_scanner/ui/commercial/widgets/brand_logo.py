"""Painted NFS brand logo widget for the commercial top header."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget


class NFSLogoWidget(QWidget):
    """Instrument-style NFS logo tile drawn entirely with QPainter."""

    LOGO_SIZE = 44

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialTitleBarLogo")
        self.setProperty("brandBlueBlock", True)
        self.setProperty("brandLogoBlue", True)
        self.setProperty("brandLogoWidget", True)
        self.setFixedSize(self.LOGO_SIZE, self.LOGO_SIZE)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -2, -2)

        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0.0, QColor("#0EA5FF"))
        gradient.setColorAt(0.5, QColor("#0284C7"))
        gradient.setColorAt(1.0, QColor("#1D4ED8"))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#075985"), 1.2))
        painter.drawRoundedRect(rect, 9, 9)

        highlight = QLinearGradient(rect.topLeft(), rect.bottomRight())
        highlight.setColorAt(0.0, QColor(255, 255, 255, 55))
        highlight.setColorAt(0.35, QColor(255, 255, 255, 0))
        painter.setBrush(highlight)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -int(rect.height() * 0.45)), 8, 8)

        inner_shadow = rect.adjusted(2, 2, -2, -2)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(7, 89, 133, 120), 1))
        painter.drawRoundedRect(inner_shadow, 7, 7)

        self._draw_hex_outline(painter, rect)

        font = QFont("Segoe UI", 9)
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        painter.setFont(font)
        painter.setPen(QColor("#F8FAFC"))
        text_rect = rect.adjusted(0, int(rect.height() * 0.34), 0, -2)
        painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter), "NFS")

        painter.end()

    @staticmethod
    def _draw_hex_outline(painter: QPainter, rect) -> None:
        cx = rect.center().x()
        cy = rect.center().y() - 2
        radius = min(rect.width(), rect.height()) * 0.22
        points: list[QPointF] = []
        for index in range(6):
            angle = math.radians(60 * index - 30)
            points.append(
                QPointF(cx + radius * math.cos(angle), cy + radius * math.sin(angle))
            )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 95), 1.2))
        painter.drawPolygon(QPolygonF(points))
        inner = QPolygonF(
            [
                QPointF(
                    cx + (radius - 3) * math.cos(math.radians(60 * index - 30)),
                    cy + (radius - 3) * math.sin(math.radians(60 * index - 30)),
                )
                for index in range(6)
            ]
        )
        painter.setPen(QPen(QColor(125, 211, 252, 80), 1))
        painter.drawPolygon(inner)


# Backward-compatible alias used by earlier header iterations.
NFSBrandLogoFrame = NFSLogoWidget
