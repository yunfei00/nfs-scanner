"""Standardized button widgets for the commercial UI."""

from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QToolButton, QWidget


class _NFSButtonBase(QPushButton):
    """Shared sizing for NFS push buttons."""

    def __init__(self, text: str, object_name: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName(object_name)
        self.setMinimumHeight(32)


class NFSPrimaryButton(_NFSButtonBase):
    """Primary action button for scan start and main workflows."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, "nfsPrimaryButton", parent)


class NFSSecondaryButton(_NFSButtonBase):
    """Secondary action button for toolbar and form actions."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, "nfsSecondaryButton", parent)


class NFSDangerButton(_NFSButtonBase):
    """Destructive or stop action button."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, "nfsDangerButton", parent)


class NFSToolButton(QToolButton):
    """Compact ghost-style tool button for collapsible headers and toolbars."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("nfsToolButton")
        self.setText(text)
        self.setMinimumHeight(24)
