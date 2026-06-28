"""Camera enumeration helpers for Windows DirectShow / OpenCV."""

from __future__ import annotations

import re
import subprocess
import sys
from typing import Iterable

from .constants import DEFAULT_CAMERA_NAME
from .models import CameraInfo
from ._opencv_import import opencv_available, require_opencv


_DSHOW_DEVICE_PATTERN = re.compile(r'^\s*"([^"]+)"\s*\(video\)', re.MULTILINE)


def _list_dshow_names_via_ffmpeg() -> list[str]:
    """Return DirectShow video device names using FFmpeg, if available."""

    if sys.platform != "win32":
        return []
    try:
        completed = subprocess.run(
            [
                "ffmpeg",
                "-list_devices",
                "true",
                "-f",
                "dshow",
                "-i",
                "dummy",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []

    text = (completed.stderr or "") + (completed.stdout or "")
    names: list[str] = []
    in_video_section = False
    for line in text.splitlines():
        if "DirectShow video devices" in line:
            in_video_section = True
            continue
        if in_video_section and "DirectShow audio devices" in line:
            break
        if not in_video_section:
            continue
        stripped = line.strip()
        if stripped.startswith('"') and stripped.endswith('"'):
            names.append(stripped[1:-1])
            continue
        match = _DSHOW_DEVICE_PATTERN.search(line)
        if match:
            names.append(match.group(1))
    return names


def _probe_opencv_indices(max_index: int = 10) -> list[int]:
    """Probe DirectShow indices that OpenCV can open."""

    if not opencv_available() or sys.platform != "win32":
        return []

    cv2 = require_opencv()
    indices: list[int] = []
    for index in range(max_index):
        capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        try:
            if capture.isOpened():
                indices.append(index)
        finally:
            capture.release()
    return indices


def _merge_names_with_indices(names: Iterable[str], indices: Iterable[int]) -> list[CameraInfo]:
    """Pair FFmpeg names with OpenCV indices in enumeration order."""

    name_list = list(names)
    index_list = list(indices)
    if not index_list:
        return [CameraInfo(index=0, name=DEFAULT_CAMERA_NAME)]

    devices: list[CameraInfo] = []
    for position, index in enumerate(index_list):
        if position < len(name_list):
            devices.append(CameraInfo(index=index, name=name_list[position]))
        else:
            devices.append(CameraInfo(index=index, name=f"Camera {index}"))
    return devices


def enumerate_cameras(*, max_index: int = 10) -> list[CameraInfo]:
    """Enumerate local cameras without keeping any device open."""

    if sys.platform != "win32":
        return []

    names = _list_dshow_names_via_ffmpeg()
    indices = _probe_opencv_indices(max_index=max_index)
    devices = _merge_names_with_indices(names, indices)

    if not devices and names:
        devices = [CameraInfo(index=0, name=name) for name in names]

    if not devices:
        devices = [CameraInfo(index=0, name=DEFAULT_CAMERA_NAME)]

    return devices


def find_default_camera(devices: list[CameraInfo]) -> CameraInfo | None:
    """Return the preferred LRCP  F1080P device when present."""

    for device in devices:
        if device.name == DEFAULT_CAMERA_NAME:
            return device
    for device in devices:
        if DEFAULT_CAMERA_NAME.replace("  ", " ") in device.name.replace("  ", " "):
            return device
    return devices[0] if devices else None
