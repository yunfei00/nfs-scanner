"""Top-level commercial main shell."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QMainWindow, QScrollArea, QSizePolicy, QSplitter, QVBoxLayout, QWidget

from .bottom_dock import CommercialBottomDock
from .device_status_panel import CommercialDeviceStatusPanel
from .property_panel import CommercialPropertyPanel
from .status_bar import CommercialStatusBar
from .toolbar import CommercialToolbar
from .workspace import CommercialWorkspace
from .workflow_panel import CommercialWorkflowPanel


class CommercialMainShell(QMainWindow):
    """Commercial UI shell with toolbar, split regions and status bar."""

    LEFT_PANEL_WIDTH = 260
    RIGHT_PANEL_WIDTH = 360
    RIGHT_PANEL_MIN_WIDTH = 320
    BOTTOM_DOCK_HEIGHT = 260
    BOTTOM_DOCK_MIN_HEIGHT = 180

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialMainShell")
        self.toolbar = CommercialToolbar(self)
        self.workflow_panel = CommercialWorkflowPanel(self)
        self.device_status_panel = CommercialDeviceStatusPanel(self)
        self.workspace = CommercialWorkspace(self)
        self.property_panel = CommercialPropertyPanel(self)
        self.bottom_dock = CommercialBottomDock(self)
        self.status_bar_widget = CommercialStatusBar(self)
        self._setup_ui()
        self._apply_initial_window_size()

    def _setup_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("commercialRoot")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        root_layout.addWidget(self.toolbar, 0)
        root_layout.addWidget(self._build_body_splitter(), 1)
        root_layout.addWidget(self.status_bar_widget, 0)
        self.setCentralWidget(root)

    def _build_body_splitter(self) -> QSplitter:
        body_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        body_splitter.setObjectName("commercialBodySplitter")
        body_splitter.setChildrenCollapsible(False)
        body_splitter.setHandleWidth(4)

        body_splitter.addWidget(self._build_left_area())
        body_splitter.addWidget(self._build_center_column())
        body_splitter.setStretchFactor(0, 0)
        body_splitter.setStretchFactor(1, 1)
        body_splitter.setSizes([self.LEFT_PANEL_WIDTH, 1200])
        return body_splitter

    def _build_left_area(self) -> QScrollArea:
        left_container = QFrame(self)
        left_container.setObjectName("commercialLeftArea")
        left_container.setMinimumWidth(self.LEFT_PANEL_WIDTH)
        left_container.setMaximumWidth(self.LEFT_PANEL_WIDTH)
        left_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)
        left_layout.addWidget(self.workflow_panel)
        left_layout.addWidget(self.device_status_panel)
        left_layout.addStretch(1)

        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("commercialLeftScroll")
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidget(left_container)
        return scroll_area

    def _build_center_column(self) -> QSplitter:
        center_splitter = QSplitter(Qt.Orientation.Vertical, self)
        center_splitter.setObjectName("commercialCenterSplitter")
        center_splitter.setChildrenCollapsible(False)
        center_splitter.setHandleWidth(4)

        upper_splitter = QSplitter(Qt.Orientation.Horizontal, center_splitter)
        upper_splitter.setObjectName("commercialUpperSplitter")
        upper_splitter.setChildrenCollapsible(False)
        upper_splitter.setHandleWidth(4)

        self.workspace.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.property_panel.setMinimumWidth(self.RIGHT_PANEL_MIN_WIDTH)
        self.property_panel.setMaximumWidth(self.RIGHT_PANEL_WIDTH)

        upper_splitter.addWidget(self.workspace)
        upper_splitter.addWidget(self.property_panel)
        upper_splitter.setStretchFactor(0, 1)
        upper_splitter.setStretchFactor(1, 0)
        upper_splitter.setSizes([900, self.RIGHT_PANEL_WIDTH])

        self.bottom_dock.setMinimumHeight(self.BOTTOM_DOCK_MIN_HEIGHT)
        center_splitter.addWidget(upper_splitter)
        center_splitter.addWidget(self.bottom_dock)
        center_splitter.setStretchFactor(0, 1)
        center_splitter.setStretchFactor(1, 0)
        center_splitter.setSizes([700, self.BOTTOM_DOCK_HEIGHT])
        return center_splitter

    def _apply_initial_window_size(self) -> None:
        from PySide6.QtWidgets import QApplication

        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            self.resize(1600, 900)
            return

        available = screen.availableGeometry()
        width = min(max(int(available.width() * 0.92), 1366), available.width())
        height = min(max(int(available.height() * 0.92), 768), available.height())
        self.resize(width, height)
