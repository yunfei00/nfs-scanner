"""Simple parameter form rows for commercial UI panels."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QWidget


class ParameterForm(QWidget):
    """Form container for labeled placeholder inputs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.form_layout = QFormLayout(self)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setHorizontalSpacing(10)
        self.form_layout.setVerticalSpacing(8)

    def add_row(self, label: str, value: str = "", *, placeholder: str = "") -> QLineEdit:
        field = QLineEdit(self)
        field.setText(value)
        if placeholder:
            field.setPlaceholderText(placeholder)
        label_widget = QLabel(label, self)
        label_widget.setObjectName("commercialMutedLabel")
        self.form_layout.addRow(label_widget, field)
        return field
