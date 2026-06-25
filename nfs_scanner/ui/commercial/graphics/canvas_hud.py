"""HUD overlays for the realtime canvas (axes + cursor readout)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class CanvasAxisLegend(QFrame):
    """Bottom-left axis legend with X/Y/Z color coding."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("canvasAxisLegend")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)
        for axis, color, name in (("X", "#EF4444", "X"), ("Y", "#22C55E", "Y"), ("Z", "#3B82F6", "Z")):
            chip = QLabel(f"{name}", self)
            chip.setObjectName("canvasAxisChip")
            chip.setProperty("axisColor", color)
            chip.style().unpolish(chip)
            chip.style().polish(chip)
            layout.addWidget(chip)


class CanvasCursorHud(QFrame):
    """Top-left cursor coordinate and measurement readout."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("canvasCursorHud")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        self._pos_label = QLabel("X: --  Y: --  Z: --", self)
        self._pos_label.setObjectName("canvasCursorPos")
        self._rf_label = QLabel("Freq: --  Amp: --", self)
        self._rf_label.setObjectName("canvasCursorRf")
        layout.addWidget(self._pos_label)
        layout.addWidget(self._rf_label)

    def update_readout(
        self,
        *,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
        freq: str = "--",
        amp: str = "--",
    ) -> None:
        if x is None or y is None:
            self._pos_label.setText("X: --  Y: --  Z: --")
        else:
            z_text = f"{z:.2f}" if z is not None else "--"
            self._pos_label.setText(f"X: {x:.2f}  Y: {y:.2f}  Z: {z_text}")
        self._rf_label.setText(f"Freq: {freq}  Amp: {amp}")
