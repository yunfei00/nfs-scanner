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
    alternative_name: str = ""
    vid_pid: str = ""
    recommended: bool = False
    names_from_ffmpeg: bool = True
    backend: str = "DirectShow"

    def display_name(self) -> str:
        """Return a user-facing combo-box label."""

        label = f"{self.name} (#{self.index}"
        if self.vid_pid:
            label += f", {self.vid_pid}"
        if self.recommended:
            label += ", Recommended"
        label += ")"
        return label

    def details_text(self) -> str:
        """Return multi-line details for the selected device panel."""

        lines = [
            "当前选择设备：",
            f"Name: {self.name}",
            f"Index: {self.index}",
        ]
        if self.vid_pid:
            lines.append(f"VID/PID: {self.vid_pid}")
        elif self.alternative_name:
            lines.append(f"Alternative: {self.alternative_name}")
        else:
            lines.append("VID/PID: (unknown)")
        lines.append(f"Backend: {self.backend}")
        lines.append(f"Recommended: {'Yes' if self.recommended else 'No'}")
        if not self.names_from_ffmpeg:
            lines.append("Note: FFmpeg names unavailable; showing OpenCV index only.")
        return "\n".join(lines)


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


@dataclass(frozen=True, slots=True)
class CameraEnumerationResult:
    """Outcome of one camera enumeration pass."""

    devices: list[CameraInfo]
    ffmpeg_available: bool = False
    used_ffmpeg_names: bool = False

    @property
    def warning_message(self) -> str:
        if self.ffmpeg_available and self.used_ffmpeg_names:
            return ""
        if not self.ffmpeg_available:
            return "FFmpeg not found, device names unavailable."
        return ""
