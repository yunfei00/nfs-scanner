"""Composition root for the unified desktop application."""

from __future__ import annotations

from dataclasses import dataclass

from nfs_scanner.core import DeviceManager, ScanManager


@dataclass(slots=True)
class ApplicationContext:
    """Long-lived managers shared by the unified main window."""

    device_manager: DeviceManager
    scan_manager: ScanManager


def create_application_context() -> ApplicationContext:
    """Create the application context using the proven legacy interfaces."""

    return ApplicationContext(
        device_manager=DeviceManager(),
        scan_manager=ScanManager(),
    )
