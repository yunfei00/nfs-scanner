"""Numeric input field with unit suffix for commercial UI forms."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QWidget


class NFSNumericField(QWidget):
    """Line edit with trailing unit label and valid/invalid visual state."""

    valueChanged = Signal()

    def __init__(self, unit: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("nfsNumericField")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._input = QLineEdit(self)
        self._input.setObjectName("nfsNumericInput")
        self._input.setMinimumWidth(48)
        self._input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._input, 1)

        self._unit_label = QLabel(unit, self)
        self._unit_label.setObjectName("nfsNumericUnit")
        self._unit_label.setMinimumWidth(self._unit_width(unit))
        layout.addWidget(self._unit_label, 0)

        self.setMinimumHeight(28)
        self.set_valid(True)

    @staticmethod
    def _unit_width(unit: str) -> int:
        """Return a compact suffix width so the numeric value remains readable."""

        if not unit:
            return 0
        if len(unit) <= 2:
            return 24
        if len(unit) <= 3:
            return 32
        return 46

    def _on_text_changed(self, _text: str) -> None:
        self.valueChanged.emit()

    def text(self) -> str:
        return self._input.text()

    def setText(self, value: str) -> None:
        self._input.setText(value)

    def set_unit(self, unit: str) -> None:
        self._unit_label.setText(unit)
        self._unit_label.setMinimumWidth(self._unit_width(unit))

    def set_valid(self, valid: bool) -> None:
        state = "valid" if valid else "invalid"
        self._input.setProperty("fieldState", state)
        self._input.style().unpolish(self._input)
        self._input.style().polish(self._input)

    def line_edit(self) -> QLineEdit:
        return self._input
