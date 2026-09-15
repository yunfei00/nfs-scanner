"""Centralized version constants for application/runtime artifacts."""

from __future__ import annotations

APP_NAME = "NFS Scanner"
# Single source of truth for the application, window title, package metadata,
# installer and UI. Bump this value together with each release/tag.
APP_VERSION = "1.0.4"
BUILD_VERSION = "2026.09.15"
DATA_FORMAT_VERSION = "1.0"
CONFIG_VERSION = "1.0"
PLUGIN_API_VERSION = "1.0"

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "BUILD_VERSION",
    "CONFIG_VERSION",
    "DATA_FORMAT_VERSION",
    "PLUGIN_API_VERSION",
]
