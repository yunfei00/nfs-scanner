"""Commercial V1 helpers for simulation vs real device provider selection."""

from __future__ import annotations

import os

from nfs_scanner.config.devices_loader import DEVICES_CONFIG_YAML, DevicesConfig, resolve_device_mode
from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR, is_real_device_control_allowed


def is_commercial_real_bridge_configured(config: DevicesConfig) -> bool:
    """Return True when config and env request real device bridge (not yet connected)."""

    env_mode = os.getenv("NFS_SCANNER_DEVICE_MODE", "").strip().lower()
    if env_mode == "real" and config.mode == "real":
        return True
    return resolve_device_mode(config) == "real" and config.mode == "real"


def is_commercial_real_bridge_armed(config: DevicesConfig) -> bool:
    """Return True when real bridge is configured and NFS_SCANNER_REAL_DEVICES allows I/O."""

    return is_commercial_real_bridge_configured(config) and is_real_device_control_allowed()


def commercial_device_mode_label(config: DevicesConfig, *, real_mode_confirmed: bool = False) -> str:
    """Human-readable mode label for Device Center / status bar."""

    if not is_real_device_control_allowed():
        return "Real Disabled"
    if is_commercial_real_bridge_configured(config):
        if real_mode_confirmed:
            return "Real Device Connected"
        return "Real Armed"
    return "Simulation"


def real_device_block_message() -> str:
    return (
        f"Real device control disabled — set {REAL_DEVICE_ENV_VAR}=1, "
        f"NFS_SCANNER_DEVICE_MODE=real, and {DEVICES_CONFIG_YAML} mode: real"
    )
