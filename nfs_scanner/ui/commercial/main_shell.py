"""Top-level commercial main shell placeholder."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget

from .bottom_dock import CommercialBottomDock
from .device_status_panel import CommercialDeviceStatusPanel
from .property_panel import CommercialPropertyPanel
from .status_bar import CommercialStatusBar
from .toolbar import CommercialToolbar
from .widgets import CommercialCard
from .workspace import CommercialWorkspace
from .workflow_panel import CommercialWorkflowPanel


class CommercialMainShell(QWidget):
    """Commercial UI shell placeholder. Layout is expanded in later sprint tasks."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialMainShell")
        self.toolbar = CommercialToolbar(self)
        self.workflow_panel = CommercialWorkflowPanel(self)
        self.device_status_panel = CommercialDeviceStatusPanel(self)
        self.workspace = CommercialWorkspace(self)
        self.property_panel = CommercialPropertyPanel(self)
        self.bottom_dock = CommercialBottomDock(self)
        self.status_bar = CommercialStatusBar(self)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)

        preview_card = CommercialCard("Theme Preview", self)
        tabs = QTabWidget(preview_card.body)
        tabs.addTab(self._create_preview_page("Buttons"), "Controls")
        tabs.addTab(self._create_preview_page("Cards / Tabs"), "Panels")
        preview_card.body_layout.addWidget(tabs)
        layout.addWidget(preview_card, 1)

    def _create_preview_page(self, text: str) -> QWidget:
        page = QWidget(self)
        page_layout = QVBoxLayout(page)
        label = QLabel(text, page)
        label.setObjectName("commercialMutedLabel")
        page_layout.addWidget(label)
        return page
