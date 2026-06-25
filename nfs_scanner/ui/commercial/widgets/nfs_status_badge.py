"""Status badge widget for device and workflow states."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget

_BADGE_STATUSES = frozenset({"connected", "disconnected", "warning", "error", "running"})
_LEGACY_STATUS_ALIASES = {"scanning": "running"}


class NFSStatusBadge(QLabel):
    """Small status label styled through QSS dynamic property."""

    def __init__(self, text: str, status: str = "disconnected", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("nfsStatusBadge")
        self.set_status(status)

    def set_status(self, status: str) -> None:
        """Update badge styling via the ``badgeStatus`` dynamic property."""

        normalized = _LEGACY_STATUS_ALIASES.get(status, status)
        if normalized not in _BADGE_STATUSES:
            normalized = "disconnected"
        self.setProperty("badgeStatus", normalized)
        self.style().unpolish(self)
        self.style().polish(self)
