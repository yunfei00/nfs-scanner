"""Integration safety guards before real device control."""

from __future__ import annotations

import os

REAL_DEVICE_ENV_VAR = "NFS_SCANNER_REAL_DEVICES"

# Default: real device control is disabled.
REAL_DEVICE_ENABLED = False


def is_real_device_control_allowed() -> bool:
    """Return whether real hardware control is explicitly enabled."""

    env_value = os.getenv(REAL_DEVICE_ENV_VAR, "").strip().lower()
    if env_value in ("1", "true", "yes", "on"):
        return True
    return REAL_DEVICE_ENABLED


class RealDeviceControlBlockedError(RuntimeError):
    """Raised when real device control is requested while disabled."""


def require_real_device_control(operation: str) -> None:
    """Guard real device entry points; raises when control is not allowed."""

    if not is_real_device_control_allowed():
        raise RealDeviceControlBlockedError(
            f"Real device control is disabled for operation: {operation}. "
            f"Set {REAL_DEVICE_ENV_VAR}=1 only after Major Review approval."
        )
