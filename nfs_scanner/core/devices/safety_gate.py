"""Safety gate for real device commands (default: simulation only)."""

from __future__ import annotations

from dataclasses import dataclass

from nfs_scanner.core.integration_safety import (
    RealDeviceControlBlockedError,
    is_real_device_control_allowed,
)


@dataclass(slots=True)
class SafetyGate:
    """Gate all hardware-bound operations; simulation bypasses when dry_run=True."""

    @staticmethod
    def allow_motion_command(*, operation: str, dry_run: bool = True) -> None:
        if dry_run:
            return
        if not is_real_device_control_allowed():
            raise RealDeviceControlBlockedError(
                f"Motion command blocked: {operation}. Real devices disabled."
            )

    @staticmethod
    def allow_spectrum_command(*, operation: str, dry_run: bool = True) -> None:
        if dry_run:
            return
        if not is_real_device_control_allowed():
            raise RealDeviceControlBlockedError(
                f"Spectrum command blocked: {operation}. Real devices disabled."
            )

    @staticmethod
    def allow_camera_command(*, operation: str, dry_run: bool = True) -> None:
        if dry_run:
            return
        if not is_real_device_control_allowed():
            raise RealDeviceControlBlockedError(
                f"Camera command blocked: {operation}. Real devices disabled."
            )
