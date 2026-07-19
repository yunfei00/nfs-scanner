"""Persistent application-configuration helpers."""

from __future__ import annotations

import json
import logging
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from nfs_scanner.application.paths import AppPaths
from nfs_scanner.core.versioning import is_major_compatible, safe_version_str
from nfs_scanner.storage.atomic import atomic_write_json
from nfs_scanner.version import CONFIG_VERSION

LOGGER = logging.getLogger(__name__)
CONFIG_PATH_ENV_VAR = "NFS_SCANNER_CONFIG_PATH"
SCAN_MODE_VALUES = {"raster", "snake"}
DEFAULT_CONFIG: dict[str, Any] = {
    "config_version": CONFIG_VERSION,
    "scan": {
        "start_x": "0",
        "stop_x": "4",
        "step_x": "1",
        "start_y": "-4",
        "stop_y": "0",
        "step_y": "1",
        "scan_mode": "snake",
    },
    "spectrum_start_freq": "100MHz",
    "spectrum_stop_freq": "3GHz",
    "spectrum_rbw": "100kHz",
    "spectrum_device_type": "TCPIP-SCPI",
    "heatmap_colormap": "viridis",
    "heatmap_auto_range": True,
    "heatmap_scale_min": 0.0,
    "heatmap_scale_max": 1.0,
}


def get_config_path() -> Path:
    """Return the application config file path."""

    override = os.getenv(CONFIG_PATH_ENV_VAR)
    if override:
        return Path(override).expanduser()
    return AppPaths.default().config_dir / "app_config.json"


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

    if not isinstance(payload, dict):
        payload = {}

    migrated_payload = migrate_config_if_needed(payload)
    config = _normalize_config(migrated_payload)
    LOGGER.info("[CONFIG] config loaded: version=%s", config.get("config_version"))
    return config


def save_config(config: Mapping[str, Any]) -> None:
    """Save persisted UI configuration to disk."""

    config_path = get_config_path()
    normalized_config = _normalize_config(dict(config))
    normalized_config["config_version"] = safe_version_str(
        normalized_config.get("config_version"),
        default=CONFIG_VERSION,
    )
    config_path.parent.mkdir(parents=True, exist_ok=True)

    atomic_write_json(config_path, normalized_config)

    LOGGER.info("[CONFIG] config saved: version=%s", normalized_config.get("config_version"))


def migrate_config_if_needed(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Migrate old config payloads to the current schema baseline.

    Current stage only performs tolerant bootstrapping and logging.
    Future versions can add keyed migration handlers here.
    """

    migrated = deepcopy(config_dict)
    stored_version = safe_version_str(migrated.get("config_version"), default=CONFIG_VERSION)
    if "config_version" not in migrated:
        LOGGER.warning(
            "[CONFIG] missing config_version, fallback=%s; treating as legacy payload.",
            CONFIG_VERSION,
        )
        migrated["config_version"] = CONFIG_VERSION
        return migrated

    migrated["config_version"] = stored_version
    if stored_version != CONFIG_VERSION:
        LOGGER.warning(
            "[CONFIG] version mismatch: current=%s, loaded=%s. Migration entry reserved.",
            CONFIG_VERSION,
            stored_version,
        )
        if not is_major_compatible(CONFIG_VERSION, stored_version):
            LOGGER.warning(
                "[CONFIG] major version differs (current=%s loaded=%s); running compatibility mode.",
                CONFIG_VERSION,
                stored_version,
            )

    return migrated


def _normalize_config(payload: Any) -> dict[str, Any]:
    """Return a safe configuration payload with known fields only."""

    config = deepcopy(DEFAULT_CONFIG)
    if not isinstance(payload, dict):
        return config

    config["config_version"] = safe_version_str(payload.get("config_version"), default=CONFIG_VERSION)

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

    heatmap_colormap = payload.get("heatmap_colormap")
    if isinstance(heatmap_colormap, str) and heatmap_colormap.strip():
        config["heatmap_colormap"] = heatmap_colormap.strip()

    heatmap_auto_range = payload.get("heatmap_auto_range")
    if isinstance(heatmap_auto_range, bool):
        config["heatmap_auto_range"] = heatmap_auto_range
    elif isinstance(heatmap_auto_range, str):
        normalized_auto_range = heatmap_auto_range.strip().lower()
        if normalized_auto_range in {"true", "1", "yes", "on"}:
            config["heatmap_auto_range"] = True
        elif normalized_auto_range in {"false", "0", "no", "off"}:
            config["heatmap_auto_range"] = False

    for field_name in ("heatmap_scale_min", "heatmap_scale_max"):
        value = payload.get(field_name)
        if value is None:
            continue
        try:
            config[field_name] = float(value)
        except (TypeError, ValueError):
            continue

    return config
