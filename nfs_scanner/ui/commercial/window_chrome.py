"""Windows-native window chrome helpers for the commercial UI."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QWidget

_logger = logging.getLogger(__name__)

# Windows 10 1809+ / Windows 11 immersive dark title bar attribute.
_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19


def apply_dark_title_bar(window: QWidget) -> bool:
    """Request a dark native title bar on Windows (no-op elsewhere).

    Uses ``DwmSetWindowAttribute`` with immersive dark mode. Falls back to the
    legacy attribute value on older Windows 10 builds. Never raises.
    """

    if sys.platform != "win32":
        return False

    try:
        window_handle = int(window.winId())
    except (AttributeError, TypeError, ValueError):
        return False

    if window_handle <= 0:
        return False

    try:
        import ctypes

        dwmapi = ctypes.windll.dwmapi
        enabled = ctypes.c_int(1)
        for attribute in (_DWMWA_USE_IMMERSIVE_DARK_MODE, _DWMWA_USE_IMMERSIVE_DARK_MODE_OLD):
            result = dwmapi.DwmSetWindowAttribute(
                window_handle,
                attribute,
                ctypes.byref(enabled),
                ctypes.sizeof(enabled),
            )
            if result == 0:
                _logger.debug("Dark title bar applied (DWM attribute %s)", attribute)
                return True
        _logger.debug("DwmSetWindowAttribute dark mode not supported on this Windows build")
        return False
    except Exception as error:
        _logger.debug("Dark title bar skipped: %s", error)
        return False
