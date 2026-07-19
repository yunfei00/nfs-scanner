"""Unified main window for the Near Field Scan System."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QSizeGrip, QVBoxLayout, QWidget

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
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setMinimumSize(self.MINIMUM_WIDTH, self.MINIMUM_HEIGHT)
        self._resize_for_available_screen()
        self._setup_ui()

    def _resize_for_available_screen(self) -> None:
        """Keep the initial frameless window and its controls inside the desktop."""

        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
            return
        available = screen.availableGeometry()
        width = min(self.DEFAULT_WIDTH, max(self.MINIMUM_WIDTH, int(available.width() * 0.94)))
        height = min(self.DEFAULT_HEIGHT, max(self.MINIMUM_HEIGHT, int(available.height() * 0.94)))
        self.resize(width, height)
        self.move(
            available.x() + max((available.width() - width) // 2, 0),
            available.y() + max((available.height() - height) // 2, 0),
        )

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
        self.size_grip = QSizeGrip(central_widget)
        self.size_grip.setObjectName("windowSizeGrip")
        self.size_grip.setFixedSize(18, 18)
        self.size_grip.raise_()
        self.setDockOptions(QMainWindow.DockOption.AnimatedDocks)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

    def changeEvent(self, event: QEvent) -> None:
        """Synchronize custom chrome when Windows changes the window state."""

        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self.header.sync_window_state()
            self.size_grip.setVisible(not self.isMaximized())

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Keep the frameless resize grip anchored to the lower-right corner."""

        super().resizeEvent(event)
        margin = 3
        self.size_grip.move(
            self.centralWidget().width() - self.size_grip.width() - margin,
            self.centralWidget().height() - self.size_grip.height() - margin,
        )
        self.size_grip.raise_()
