"""Safe entry point for the commercial UI shell."""

from __future__ import annotations

import os

from PySide6.QtWidgets import QWidget

from .main_shell import CommercialMainShell
from .theme import apply_commercial_theme

COMMERCIAL_UI_ENV_VAR = "NFS_SCANNER_UI"


def is_commercial_ui_enabled() -> bool:
    """Return whether the commercial UI should be used at startup."""

    return os.getenv(COMMERCIAL_UI_ENV_VAR, "").strip().lower() == "commercial"


def create_commercial_shell(parent: QWidget | None = None) -> CommercialMainShell:
    """Create the commercial main shell without affecting legacy startup."""

    shell = CommercialMainShell(parent)
    apply_commercial_theme(shell)
    return shell
