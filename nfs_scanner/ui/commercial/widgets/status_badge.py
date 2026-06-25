"""Status badge widget for device and workflow states."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget

_STATUS_OBJECT_NAMES = {
    "connected": "statusBadgeConnected",
    "disconnected": "statusBadgeDisconnected",
    "scanning": "statusBadgeScanning",
    "error": "statusBadgeError",
}


class StatusBadge(QLabel):
    """Small status label styled through QSS object names."""

    def __init__(self, text: str, status: str = "disconnected", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.set_status(status)

    def set_status(self, status: str) -> None:
        """Update badge text styling via object name."""

        object_name = _STATUS_OBJECT_NAMES.get(status, "statusBadgeDisconnected")
        self.setObjectName(object_name)
