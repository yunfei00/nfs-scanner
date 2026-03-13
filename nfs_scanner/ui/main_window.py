"""Main window assembly for the Near Field Scan System."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QVBoxLayout, QWidget

from .controls_panel import ControlsPanel
from .heatmap_view import HeatmapView
from .log_panel import LogPanel
from .spectrum_panel import SpectrumPanel


class MainWindow(QMainWindow):
    """Application main window that assembles high-level UI regions."""

    def __init__(self) -> None:
        super().__init__()
        self.controls_panel: ControlsPanel
        self.heatmap_view: HeatmapView
        self.spectrum_panel: SpectrumPanel
        self.log_panel: LogPanel
        self.setWindowTitle("近场扫描系统")
        self.resize(1600, 900)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Assemble the main application layout from UI components."""

        central_widget = QWidget(self)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        top_splitter = QSplitter(Qt.Orientation.Horizontal, central_widget)
        bottom_splitter = QSplitter(Qt.Orientation.Vertical, central_widget)

        self.controls_panel = ControlsPanel()
        self.heatmap_view = HeatmapView()
        self.spectrum_panel = SpectrumPanel()
        self.log_panel = LogPanel()

        top_splitter.addWidget(self.controls_panel)
        top_splitter.addWidget(self.heatmap_view)
        top_splitter.addWidget(self.spectrum_panel)

        top_splitter.setStretchFactor(0, 0)
        top_splitter.setStretchFactor(1, 1)
        top_splitter.setStretchFactor(2, 0)
        top_splitter.setSizes([320, 900, 320])

        bottom_splitter.addWidget(top_splitter)
        bottom_splitter.addWidget(self.log_panel)
        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 0)
        bottom_splitter.setSizes([700, 180])

        root_layout.addWidget(bottom_splitter)
        self.setCentralWidget(central_widget)

        self.statusBar().showMessage("系统就绪")
        self.log_panel.append_log("系统启动，基础界面已加载。")
