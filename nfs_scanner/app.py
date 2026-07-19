"""Application bootstrap for the Near Field Scan System."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from .application import AppPaths, create_application_context
from .infra import install_exception_hook
from .infra.logging_config import get_logger, setup_logging
from .ui.main_window import MainWindow
from .ui.theme import apply_theme
from .version import APP_NAME, APP_VERSION


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create the Qt application instance."""

    arguments = list(argv) if argv is not None else sys.argv
    app = QApplication(arguments)
    app.setApplicationName(f"{APP_NAME} v{APP_VERSION}")
    app.setOrganizationName("nfs-scanner")
    apply_theme(app)
    return app


def main(argv: Sequence[str] | None = None) -> int:
    """Start the desktop application."""

    paths = AppPaths.default()
    paths.ensure_runtime_directories()
    paths.migrate_legacy_runtime_files()
    log_file = setup_logging(force=True, log_directory=paths.log_dir)
    logger = get_logger(__name__)
    install_exception_hook(logger)
    logger.info("应用启动，日志文件：%s", log_file)

    app = create_application(argv)
    instance_lock = QLockFile(str(paths.state_dir / "nfs-scanner.lock"))
    instance_lock.setStaleLockTime(30_000)
    if not instance_lock.tryLock(100):
        logger.warning("应用启动被拒绝：已有实例正在运行")
        QMessageBox.warning(None, "NFS Scanner", "NFS Scanner 已在运行，请先切换到现有窗口。")
        return 2
    logger.info("启动统一主界面")
    context = create_application_context(paths=paths)
    window = MainWindow(context=context)
    app.aboutToQuit.connect(window.shutdown)
    window.show()

    auto_close_ms = os.getenv("NFS_SCANNER_AUTOCLOSE_MS")
    if auto_close_ms:
        QTimer.singleShot(int(auto_close_ms), app.quit)

    exit_code = app.exec()
    instance_lock.unlock()
    logger.info("应用退出，退出码：%s", exit_code)
    return exit_code
