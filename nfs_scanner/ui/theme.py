"""Theme loading for the unified engineering interface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

THEME_PATH = Path(__file__).resolve().parents[2] / "resources" / "styles" / "engineering_dark.qss"
APP_ICON_PATH = Path(__file__).resolve().parents[2] / "resources" / "icons" / "nfs_scanner.svg"


def load_theme() -> str:
    """Load the application stylesheet from the repository resources."""

    try:
        return THEME_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def apply_theme(app: QApplication) -> None:
    """Apply the single supported application theme."""

    app.setStyle("Fusion")
    app.setStyleSheet(load_theme())
    if APP_ICON_PATH.is_file():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
