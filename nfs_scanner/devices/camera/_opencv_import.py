"""Lazy OpenCV import helper."""

from __future__ import annotations

from typing import Any


def require_opencv() -> Any:
    """Import OpenCV or raise a clear installation error."""

    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "USB camera support requires opencv-python. Install with: pip install opencv-python"
        ) from exc
    return cv2


def opencv_available() -> bool:
    """Return True when OpenCV can be imported."""

    try:
        require_opencv()
    except ImportError:
        return False
    return True
