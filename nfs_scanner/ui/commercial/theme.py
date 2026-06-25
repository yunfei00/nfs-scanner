"""Theme loader for the commercial UI shell."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication, QWidget

THEME_NAME = "dark_professional"
_DEFAULT_STYLE_PATH = (
    Path(__file__).resolve().parents[3] / "resources" / "styles" / f"{THEME_NAME}.qss"
)


def get_theme_path(theme_name: str = THEME_NAME) -> Path:
    """Return the QSS file path for one commercial theme."""

    return _DEFAULT_STYLE_PATH.parent / f"{theme_name}.qss"


def load_stylesheet(theme_name: str = THEME_NAME) -> str:
    """Load one commercial theme stylesheet from disk."""

    theme_path = get_theme_path(theme_name)
    if not theme_path.exists():
        return ""
    return theme_path.read_text(encoding="utf-8")


def apply_commercial_theme(widget: QWidget, *, theme_name: str = THEME_NAME) -> None:
    """Apply the commercial theme to one widget subtree."""

    stylesheet = load_stylesheet(theme_name)
    if stylesheet:
        widget.setStyleSheet(stylesheet)


def apply_commercial_theme_to_app(app: QApplication | None = None, *, theme_name: str = THEME_NAME) -> None:
    """Apply the commercial theme at application level when safe."""

    application = app or QApplication.instance()
    if application is None:
        return

    stylesheet = load_stylesheet(theme_name)
    if stylesheet:
        application.setStyleSheet(stylesheet)
