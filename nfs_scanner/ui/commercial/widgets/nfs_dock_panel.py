"""Dock panel with tabbed content for spectrum, statistics and logs."""

from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget


class NFSDockPanel(QWidget):
    """Bottom dock region using tabs for compact layouts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("nfsDockPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("nfsDockTabs")
        layout.addWidget(self.tab_widget, 1)

    def add_tab(self, widget: QWidget, title: str) -> int:
        """Add a tab page and return its index."""

        return self.tab_widget.addTab(widget, title)
