"""Shared camera data models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CameraState(str, Enum):
    """High-level camera connection / preview state."""

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    PREVIEWING = "previewing"
    ERROR = "error"

    @property
    def label_zh(self) -> str:
        """Return a short Chinese label for UI display."""

        return {
            CameraState.DISCONNECTED: "未连接",
            CameraState.CONNECTED: "已连接",
            CameraState.PREVIEWING: "预览中",
            CameraState.ERROR: "错误",
        }[self]

    @property
    def badge_status(self) -> str:
        """Map to ``NFSStatusBadge`` status tokens."""

        return {
            CameraState.DISCONNECTED: "disconnected",
            CameraState.CONNECTED: "connected",
            CameraState.PREVIEWING: "running",
            CameraState.ERROR: "error",
        }[self]


@dataclass(frozen=True, slots=True)
class CameraInfo:
    """One enumerated camera entry."""

    index: int
    name: str

    def display_name(self) -> str:
        """Return a user-facing label including the DirectShow index."""

        return f"{self.name} (#{self.index})"


@dataclass(frozen=True, slots=True)
class CameraProfile:
    """Capture profile applied when opening a camera."""

    width: int
    height: int
    fps: int
    fourcc: str = "MJPG"

    @property
    def resolution_label(self) -> str:
        return f"{self.width}x{self.height}"
