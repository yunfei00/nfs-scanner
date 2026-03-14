"""Persistent application-configuration helpers."""

from __future__ import annotations

import json
import logging
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

LOGGER = logging.getLogger(__name__)
CONFIG_PATH_ENV_VAR = "NFS_SCANNER_CONFIG_PATH"
SCAN_MODE_VALUES = {"raster", "snake"}
DEFAULT_CONFIG: dict[str, Any] = {
    "scan": {
        "start_x": "0",
        "stop_x": "4",
        "step_x": "1",
        "start_y": "0",
        "stop_y": "4",
        "step_y": "1",
        "scan_mode": "snake",
    },
    "spectrum_start_freq": "100MHz",
    "spectrum_stop_freq": "3GHz",
    "spectrum_rbw": "100kHz",
    "spectrum_device_type": "TCPIP-SCPI",
}


def get_config_path() -> Path:
    """Return the application config file path."""

    override = os.getenv(CONFIG_PATH_ENV_VAR)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".nfs_scanner" / "config.json"


def load_config() -> dict[str, Any]:
    """Load persisted UI configuration from disk."""

    config_path = get_config_path()
    payload: Any = {}

    try:
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
    except (OSError, json.JSONDecodeError):
        payload = {}

    config = _normalize_config(payload)
    LOGGER.info("[CONFIG] config loaded")
    return config


def save_config(config: Mapping[str, Any]) -> None:
    """Save persisted UI configuration to disk."""

    config_path = get_config_path()
    normalized_config = _normalize_config(dict(config))
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with config_path.open("w", encoding="utf-8") as file:
        json.dump(normalized_config, file, ensure_ascii=False, indent=2)

    LOGGER.info("[CONFIG] config saved")


def _normalize_config(payload: Any) -> dict[str, Any]:
    """Return a safe configuration payload with known fields only."""

    config = deepcopy(DEFAULT_CONFIG)
    if not isinstance(payload, dict):
        return config

    scan_settings = payload.get("scan")
    if isinstance(scan_settings, dict):
        for field_name in ("start_x", "stop_x", "step_x", "start_y", "stop_y", "step_y"):
            value = scan_settings.get(field_name)
            if value is not None:
                config["scan"][field_name] = str(value)

        scan_mode = scan_settings.get("scan_mode")
        if isinstance(scan_mode, str) and scan_mode in SCAN_MODE_VALUES:
            config["scan"]["scan_mode"] = scan_mode

    for field_name in ("spectrum_start_freq", "spectrum_stop_freq", "spectrum_rbw"):
        value = payload.get(field_name)
        if value is not None:
            config[field_name] = str(value)

    spectrum_device_type = payload.get("spectrum_device_type")
    if isinstance(spectrum_device_type, str) and spectrum_device_type.strip():
        config["spectrum_device_type"] = spectrum_device_type.strip()
    else:
        last_device_selection = payload.get("last_device_selection")
        if isinstance(last_device_selection, str) and last_device_selection.strip():
            config["spectrum_device_type"] = last_device_selection.strip()

    return config
