"""LUT color bar widget for realtime visualization."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QLinearGradient, QPainter
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ColorBar(QWidget):
    """Vertical color bar showing a mock dBm range."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialColorBar")
        self._min_db = -80.0
        self._max_db = -20.0
        self._lut_name = "viridis"
        self.setMinimumWidth(56)
        self.setMaximumWidth(72)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("dBm", self)
        title.setObjectName("commercialMutedLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.max_label = QLabel(f"{self._max_db:.0f}", self)
        self.max_label.setObjectName("commercialValueLabel")
        self.max_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gradient_widget = _GradientBar(self)
        self.min_label = QLabel(f"{self._min_db:.0f}", self)
        self.min_label.setObjectName("commercialValueLabel")
        self.min_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lut_label = QLabel(self._lut_name, self)
        self.lut_label.setObjectName("commercialMutedLabel")
        self.lut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(self.max_label)
        layout.addWidget(self.gradient_widget, 1)
        layout.addWidget(self.min_label)
        layout.addWidget(self.lut_label)

    def set_range(self, minimum_db: float, maximum_db: float) -> None:
        self._min_db = minimum_db
        self._max_db = maximum_db
        self.min_label.setText(f"{minimum_db:.0f}")
        self.max_label.setText(f"{maximum_db:.0f}")
        self.gradient_widget.update()

    def set_lut_name(self, lut_name: str) -> None:
        self._lut_name = lut_name.strip() or "viridis"
        self.lut_label.setText(self._lut_name)


class _GradientBar(QWidget):
    """Internal gradient paint area."""

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, Qt.GlobalColor.yellow)
        gradient.setColorAt(0.5, Qt.GlobalColor.cyan)
        gradient.setColorAt(1.0, Qt.GlobalColor.blue)
        painter.fillRect(self.rect(), gradient)
        painter.end()
        super().paintEvent(event)
