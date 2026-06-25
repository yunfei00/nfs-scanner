"""Parameter group widget for labeled form rows."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from .nfs_numeric_field import NFSNumericField


class NFSParameterGroup(QWidget):
    """Form container with optional title and description."""

    def __init__(
        self,
        title: str = "",
        description: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("nfsParameterGroup")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        if title:
            title_label = QLabel(title, self)
            title_label.setObjectName("nfsSectionTitle")
            layout.addWidget(title_label)

        if description:
            description_label = QLabel(description, self)
            description_label.setObjectName("nfsMutedLabel")
            description_label.setWordWrap(True)
            layout.addWidget(description_label)

        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setHorizontalSpacing(10)
        self.form_layout.setVerticalSpacing(8)
        layout.addLayout(self.form_layout)

    def add_row(self, label: str, value: str = "", *, placeholder: str = "") -> QLineEdit:
        """Add a labeled input row and return the field widget."""

        field = QLineEdit(self)
        field.setText(value)
        if placeholder:
            field.setPlaceholderText(placeholder)
        label_widget = QLabel(label, self)
        label_widget.setObjectName("nfsMutedLabel")
        self.form_layout.addRow(label_widget, field)
        return field

    def add_numeric_row(
        self,
        label: str,
        value: str = "",
        *,
        unit: str = "",
        placeholder: str = "",
    ) -> NFSNumericField:
        """Add a labeled numeric field with unit suffix."""

        field = NFSNumericField(unit, self)
        field.setText(value)
        if placeholder:
            field.line_edit().setPlaceholderText(placeholder)
        label_widget = QLabel(label, self)
        label_widget.setObjectName("nfsMutedLabel")
        self.form_layout.addRow(label_widget, field)
        return field
