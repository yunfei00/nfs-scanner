"""Theme handling for the unified engineering interface.

The production default deliberately follows the v1.0.3 appearance: Qt/Windows
native light colours.  v1.0.4 keeps its newer layout and widgets, but must not
force the engineering dark stylesheet over them.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

APP_ICON_PATH = Path(__file__).resolve().parents[2] / "resources" / "icons" / "nfs_scanner.svg"


def load_theme() -> str:
    """Return the production stylesheet.

    v1.0.3 did not install an application-wide QSS.  Returning an empty
    stylesheet lets Qt use the normal light/native palette and prevents a
    Windows dark-mode setting from being amplified by our former dark QSS.
    """

    return ""


def apply_theme(app: QApplication) -> None:
    """Restore the v1.0.3 native/light visual baseline."""

    app.setStyleSheet("")
    if APP_ICON_PATH.is_file():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
