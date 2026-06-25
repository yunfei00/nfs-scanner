"""Device service protocol (UI- and transport-independent)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

DeviceKind = Literal["motion", "spectrum", "camera"]

DeviceConnectionStatus = Literal["disconnected", "connecting", "connected", "error"]


@dataclass(slots=True, frozen=True)
class DeviceSummary:
    """Read-only device status for commercial UI panels."""

    device_id: str
    kind: DeviceKind
    display_name: str
    model: str
    address: str
    connection_status: DeviceConnectionStatus
    status_label: str
    badge_status: str
    summary: str
    last_message: str = ""


@runtime_checkable
class DeviceServiceProtocol(Protocol):
    """Contract for mock and future real device service implementations."""

    def list_devices(self) -> list[DeviceSummary]:
        """Return all known devices with current summary state."""

    def connect_device(self, device_id: str) -> DeviceSummary:
        """Request connection for one device."""

    def disconnect_device(self, device_id: str) -> DeviceSummary:
        """Request disconnection for one device."""

    def refresh_status(self) -> list[DeviceSummary]:
        """Refresh and return updated device summaries."""
