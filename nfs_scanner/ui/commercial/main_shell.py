"""Top-level commercial main shell placeholder."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .bottom_dock import CommercialBottomDock
from .property_panel import CommercialPropertyPanel
from .status_bar import CommercialStatusBar
from .toolbar import CommercialToolbar
from .workspace import CommercialWorkspace
from .workflow_panel import CommercialWorkflowPanel
from .device_status_panel import CommercialDeviceStatusPanel


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

        placeholder = QLabel("Commercial UI Shell (placeholder)", self)
        placeholder.setObjectName("commercialShellPlaceholder")
        layout.addWidget(placeholder)
