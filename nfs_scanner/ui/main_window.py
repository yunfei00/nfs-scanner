"""Unified main window for the Near Field Scan System."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from nfs_scanner.application import ApplicationContext, create_application_context
from nfs_scanner.version import APP_NAME, APP_VERSION

from .widgets import ScanControlPage
from .widgets.app_header import ApplicationHeader


class MainWindow(QMainWindow):
    """Single supported desktop shell using the proven scan/device interfaces."""

    DEFAULT_WIDTH = 1600
    DEFAULT_HEIGHT = 900
    MINIMUM_WIDTH = 1180
    MINIMUM_HEIGHT = 700

    def __init__(self, *, context: ApplicationContext | None = None) -> None:
        super().__init__()
        self.context = context or create_application_context()
        self.device_manager = self.context.device_manager
        self.scan_manager = self.context.scan_manager

        self.setObjectName("mainWindow")
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - 近场扫描系统")
        self.setMinimumSize(self.MINIMUM_WIDTH, self.MINIMUM_HEIGHT)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self._setup_ui()

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        central_widget.setObjectName("mainWindowCentral")
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = ApplicationHeader(central_widget)
        self.scan_control_page = ScanControlPage(
            central_widget,
            scan_manager=self.scan_manager,
            device_manager=self.device_manager,
        )

        layout.addWidget(self.header)
        layout.addWidget(self.scan_control_page, 1)
        self.setCentralWidget(central_widget)
        self.setDockOptions(QMainWindow.DockOption.AnimatedDocks)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
