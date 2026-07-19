"""Application bootstrap for the Near Field Scan System."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

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

    log_file = setup_logging(force=True)
    logger = get_logger(__name__)
    logger.info("应用启动，日志文件：%s", log_file)

    app = create_application(argv)
    logger.info("启动统一主界面")
    window = MainWindow()
    window.show()

    auto_close_ms = os.getenv("NFS_SCANNER_AUTOCLOSE_MS")
    if auto_close_ms:
        QTimer.singleShot(int(auto_close_ms), app.quit)

    exit_code = app.exec()
    logger.info("应用退出，退出码：%s", exit_code)
    return exit_code
