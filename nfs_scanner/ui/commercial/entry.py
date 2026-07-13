"""Safe entry point for the commercial UI shell."""

from __future__ import annotations

import os

from PySide6.QtWidgets import QWidget

from .main_shell import CommercialMainShell
from .services import CommercialServiceBundle, create_commercial_services
from .theme import apply_commercial_theme

COMMERCIAL_UI_ENV_VAR = "NFS_SCANNER_UI"


def is_commercial_ui_enabled() -> bool:
    """Return whether the commercial UI should be used at startup.

    Commercial UI is the default. ``NFS_SCANNER_UI=legacy`` explicitly keeps
    the original UI available for compatibility debugging.
    """

    return os.getenv(COMMERCIAL_UI_ENV_VAR, "commercial").strip().lower() != "legacy"


def create_commercial_shell(
    parent: QWidget | None = None,
    *,
    services: CommercialServiceBundle | None = None,
) -> CommercialMainShell:
    """Create the commercial main shell without affecting legacy startup."""

    bundle = services or create_commercial_services()
    shell = CommercialMainShell(parent, services=bundle)
    apply_commercial_theme(shell)
    return shell
