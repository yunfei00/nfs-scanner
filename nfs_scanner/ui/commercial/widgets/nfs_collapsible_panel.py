"""Collapsible panel widget for commercial UI sections."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .nfs_buttons import NFSToolButton


class NFSCollapsiblePanel(QFrame):
    """Section container that can collapse for compact layouts."""

    toggled = Signal(bool)

    def __init__(
        self,
        title: str,
        body_widget: QWidget,
        *,
        expanded: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("nfsCollapsiblePanel")
        self._expanded = expanded
        self._body_widget = body_widget
        self._setup_ui(title)
        self.set_expanded(expanded)

    def _setup_ui(self, title: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title, header)
        self.title_label.setObjectName("nfsSectionTitle")
        self.toggle_button = NFSToolButton("▾", header)
        self.toggle_button.clicked.connect(lambda: self.set_expanded(not self._expanded))

        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self.toggle_button)
        layout.addWidget(header)
        layout.addWidget(self._body_widget)

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = expanded
        self._body_widget.setVisible(expanded)
        self.toggle_button.setText("▾" if expanded else "▸")
        self.toggled.emit(expanded)
