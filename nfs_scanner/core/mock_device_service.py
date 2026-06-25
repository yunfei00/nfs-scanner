"""Mock device service for commercial UI (no real hardware)."""

from __future__ import annotations

from dataclasses import replace

from .device_service import DeviceConnectionStatus, DeviceServiceProtocol, DeviceSummary


def _badge_for_status(status: DeviceConnectionStatus) -> tuple[str, str]:
    mapping: dict[DeviceConnectionStatus, tuple[str, str]] = {
        "disconnected": ("未连接", "disconnected"),
        "connecting": ("连接中", "warning"),
        "connected": ("已连接", "connected"),
        "error": ("错误", "error"),
    }
    return mapping.get(status, ("未知", "disconnected"))


class MockDeviceService(DeviceServiceProtocol):
    """In-memory device registry with fake connect/disconnect actions."""

    def __init__(self) -> None:
        self._devices: dict[str, DeviceSummary] = {
            "motion-001": DeviceSummary(
                device_id="motion-001",
                kind="motion",
                display_name="运动平台",
                model="GRBL / Serial",
                address="COM3 @ 115200",
                connection_status="connected",
                status_label="已连接",
                badge_status="connected",
                summary="X=0.00 Y=0.00 Z=5.00",
                last_message="Mock motion platform ready",
            ),
            "spectrum-001": DeviceSummary(
                device_id="spectrum-001",
                kind="spectrum",
                display_name="频谱仪",
                model="TCPIP-SCPI",
                address="192.168.1.100",
                connection_status="disconnected",
                status_label="未连接",
                badge_status="disconnected",
                summary="100 MHz - 3 GHz / RBW 100 kHz",
                last_message="Waiting for mock connect",
            ),
            "camera-001": DeviceSummary(
                device_id="camera-001",
                kind="camera",
                display_name="相机",
                model="Mock Camera",
                address="USB-CAM-001",
                connection_status="disconnected",
                status_label="未连接",
                badge_status="disconnected",
                summary="1920x1080 / 30 fps",
                last_message="Waiting for mock connect",
            ),
        }

    def list_devices(self) -> list[DeviceSummary]:
        return [self._devices[key] for key in sorted(self._devices)]

    def connect_device(self, device_id: str) -> DeviceSummary:
        device = self._require_device(device_id)
        label, badge = _badge_for_status("connected")
        summary = device.summary
        message = f"Mock connected: {device.display_name}"
        if device.kind == "motion":
            summary = "X=0.00 Y=0.00 Z=5.00"
            message = "Mock motion platform connected (no serial I/O)"
        elif device.kind == "spectrum":
            summary = "100 MHz - 3 GHz / RBW 100 kHz"
            message = "Mock spectrum session opened (no VISA)"
        elif device.kind == "camera":
            summary = "1920x1080 / 30 fps"
            message = "Mock camera stream started (no USB capture)"
        updated = replace(
            device,
            connection_status="connected",
            status_label=label,
            badge_status=badge,
            summary=summary,
            last_message=message,
        )
        self._devices[device_id] = updated
        return updated

    def disconnect_device(self, device_id: str) -> DeviceSummary:
        device = self._require_device(device_id)
        label, badge = _badge_for_status("disconnected")
        updated = replace(
            device,
            connection_status="disconnected",
            status_label=label,
            badge_status=badge,
            last_message=f"Mock disconnected: {device.display_name}",
        )
        self._devices[device_id] = updated
        return updated

    def refresh_status(self) -> list[DeviceSummary]:
        for device_id, device in list(self._devices.items()):
            self._devices[device_id] = replace(
                device,
                last_message=f"Mock status refreshed at {device.display_name}",
            )
        return self.list_devices()

    def _require_device(self, device_id: str) -> DeviceSummary:
        device = self._devices.get(device_id)
        if device is None:
            raise KeyError(f"Unknown device id: {device_id}")
        return device
