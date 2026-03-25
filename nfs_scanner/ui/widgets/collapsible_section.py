"""Reusable collapsible section widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class CollapsibleSection(QWidget):
    """A section with header, summary line and expandable body content."""

    toggled = Signal(bool)

    def __init__(
        self,
        title: str,
        body_widget: QWidget,
        summary_widget: QWidget | None = None,
        expanded: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._expanded = expanded
        self._body_widget = body_widget
        self._summary_widget = summary_widget or QLabel("", self)
        self._setup_ui(title)
        self.set_expanded(expanded)

    def _setup_ui(self, title: str) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(6)

        header = QFrame(self)
        header.setObjectName("summaryBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 8, 6)

        title_label = QLabel(title, header)
        title_label.setStyleSheet("font-weight: 700;")

        self.toggle_button = QToolButton(header)
        self.toggle_button.setObjectName("toggleButton")
        self.toggle_button.setText("▾" if self._expanded else "▸")
        self.toggle_button.clicked.connect(self._on_toggle_clicked)

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.toggle_button)

        self.summary_frame = QFrame(self)
        self.summary_frame.setObjectName("summaryBar")
        summary_layout = QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(10, 4, 10, 4)
        self._summary_widget.setObjectName("sectionSummary")
        self._summary_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        summary_layout.addWidget(self._summary_widget)

        self.body_frame = QFrame(self)
        self.body_frame.setObjectName("sectionBody")
        body_layout = QVBoxLayout(self.body_frame)
        body_layout.setContentsMargins(10, 8, 10, 10)
        body_layout.addWidget(self._body_widget)

        root_layout.addWidget(header)
        root_layout.addWidget(self.summary_frame)
        root_layout.addWidget(self.body_frame)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def _on_toggle_clicked(self) -> None:
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded: bool) -> None:
        """Set expanded/collapsed state."""

        self._expanded = expanded
        self.body_frame.setVisible(expanded)
        self.summary_frame.setVisible(not expanded)
        self.toggle_button.setText("▾" if expanded else "▸")
        self.toggled.emit(expanded)

    def update_summary_text(self, text: str) -> None:
        """Update text if default summary QLabel is used."""

        if isinstance(self._summary_widget, QLabel):
            self._summary_widget.setText(text)
            self._summary_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
