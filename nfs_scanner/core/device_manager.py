"""Placeholder device coordination service."""

from __future__ import annotations

import logging


class DeviceManager:
    """Manage hardware device connection requests.

    The current implementation only records placeholder connection state and
    does not talk to any real hardware. Scan lifecycle and ETA state are
    owned by ``ScanManager``; this service is kept as a lightweight device
    connection registry for future integration work.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._device_states: dict[str, str] = {
            "motion_controller": "disconnected",
            "spectrum_device": "disconnected",
            "camera": "disconnected",
        }

    def connect_motion_controller(self) -> bool:
        """Record a placeholder motion-controller connection request."""

        return self._mark_placeholder_connection("motion_controller", "运动控制器")

    def connect_spectrum_device(self) -> bool:
        """Record a placeholder spectrum-device connection request."""

        return self._mark_placeholder_connection("spectrum_device", "频谱设备")

    def connect_camera(self) -> bool:
        """Record a placeholder camera connection request."""

        return self._mark_placeholder_connection("camera", "相机")

    def get_device_states(self) -> dict[str, str]:
        """Return a snapshot of the current placeholder device states."""

        return dict(self._device_states)

    def _mark_placeholder_connection(self, device_key: str, device_name: str) -> bool:
        """Mark one device as requested without claiming a real connection."""

        self._device_states[device_key] = "placeholder"
        self._logger.info("%s 连接请求已记录，当前仍为占位实现。", device_name)
        return False
