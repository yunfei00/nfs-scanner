"""LUT color bar widget for realtime visualization."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from nfs_scanner.ui.commercial.lut_presets import lut_gradient_stops, normalize_lut_name


class ColorBar(QWidget):
    """Vertical color bar showing a mock dBm range."""

    BAR_WIDTH = 28

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("nfsColorBar")
        self._min_db = -80.0
        self._max_db = -20.0
        self._lut_name = "Turbo"
        self.setFixedWidth(56)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        title = QLabel("dBm", self)
        title.setObjectName("nfsMutedLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.max_label = QLabel(f"{self._max_db:.0f}", self)
        self.max_label.setObjectName("nfsValueLabel")
        self.max_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gradient_widget = _GradientBar(self)
        self.gradient_widget.setFixedWidth(self.BAR_WIDTH)
        self.min_label = QLabel(f"{self._min_db:.0f}", self)
        self.min_label.setObjectName("nfsValueLabel")
        self.min_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lut_label = QLabel(self._lut_name, self)
        self.lut_label.setObjectName("nfsMutedLabel")
        self.lut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(self.max_label)
        layout.addWidget(self.gradient_widget, 1, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.min_label)
        layout.addWidget(self.lut_label)

    def set_range(self, minimum_db: float, maximum_db: float) -> None:
        self._min_db = minimum_db
        self._max_db = maximum_db
        self.min_label.setText(f"{minimum_db:.0f}")
        self.max_label.setText(f"{maximum_db:.0f}")
        self.gradient_widget.update()

    def set_lut_name(self, lut_name: str) -> None:
        self._lut_name = normalize_lut_name(lut_name)
        self.lut_label.setText(self._lut_name)
        self.gradient_widget.set_lut_name(self._lut_name)


class _GradientBar(QWidget):
    """Internal gradient paint area."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._lut_name = "Turbo"
        self.setMinimumHeight(120)

    def set_lut_name(self, lut_name: str) -> None:
        self._lut_name = normalize_lut_name(lut_name)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        for position, color in lut_gradient_stops(self._lut_name):
            gradient.setColorAt(position, QColor(color))
        painter.fillRect(self.rect(), gradient)
        painter.end()
        super().paintEvent(event)
