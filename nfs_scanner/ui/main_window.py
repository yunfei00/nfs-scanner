"""Unified main window for the Near Field Scan System."""

from __future__ import annotations

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QMessageBox, QVBoxLayout, QWidget

from nfs_scanner.application import ApplicationContext, create_application_context
from nfs_scanner.version import APP_NAME, APP_VERSION

from .widgets import ScanControlPage


class MainWindow(QMainWindow):
    """Single supported desktop shell using native PySide6/OS window chrome."""

    MINIMUM_WIDTH = 1180
    MINIMUM_HEIGHT = 700

    def __init__(self, *, context: ApplicationContext | None = None) -> None:
        super().__init__()
        self.context = context or create_application_context()
        self.device_manager = self.context.device_manager
        self.scan_manager = self.context.scan_manager

        self.setObjectName("mainWindow")
        # Keep the OS/PySide6 native title bar so minimize, maximize/restore and
        # close use the standard platform controls.
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - 近场扫描系统")
        self.setMinimumSize(self.MINIMUM_WIDTH, self.MINIMUM_HEIGHT)
        self._setup_ui()
        self._shutdown_complete = False

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        central_widget.setObjectName("mainWindowCentral")
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scan_control_page = ScanControlPage(
            central_widget,
            scan_manager=self.scan_manager,
            device_manager=self.device_manager,
            app_paths=self.context.paths,
        )
        layout.addWidget(self.scan_control_page, 1)
        self.setCentralWidget(central_widget)
        self.setDockOptions(QMainWindow.DockOption.AnimatedDocks)

    def shutdown(self) -> bool:
        """Stop background work and release application-owned resources once."""

        if self._shutdown_complete:
            return True
        if not self.scan_control_page.shutdown():
            return False
        self.context.shutdown()
        self._shutdown_complete = True
        return True

    def closeEvent(self, event: QCloseEvent) -> None:
        """Match native close behavior while preventing orphaned hardware work."""

        if self.scan_control_page.has_active_operations() and self.isVisible():
            choice = QMessageBox.question(
                self,
                "退出程序",
                "仍有设备任务正在运行。退出将先安全停止任务并关闭设备，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        if not self.shutdown():
            QMessageBox.warning(self, "暂时无法退出", "设备任务仍在收尾，请稍候后再次关闭。")
            event.ignore()
            return
        event.accept()
