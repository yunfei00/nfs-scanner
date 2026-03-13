"""Application bootstrap for the Near Field Scan System."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create the Qt application instance."""

    arguments = list(argv) if argv is not None else sys.argv
    app = QApplication(arguments)
    app.setApplicationName("Near Field Scan System")
    app.setOrganizationName("nfs-scanner")
    return app


def main(argv: Sequence[str] | None = None) -> int:
    """Start the desktop application."""

    app = create_application(argv)
    window = MainWindow()
    window.show()

    auto_close_ms = os.getenv("NFS_SCANNER_AUTOCLOSE_MS")
    if auto_close_ms:
        QTimer.singleShot(int(auto_close_ms), app.quit)

    return app.exec()
