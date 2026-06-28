"""Camera enumeration helpers for Windows DirectShow / OpenCV."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable

from .constants import (
    DEFAULT_CAMERA_NAME,
    DEFAULT_VID_PID,
    DEFAULT_VID_PID_TOKEN,
)
from .models import CameraEnumerationResult, CameraInfo
from ._opencv_import import opencv_available, require_opencv


_VID_PID_PATTERN = re.compile(r"vid_([0-9a-f]{4})&pid_([0-9a-f]{4})", re.IGNORECASE)
_ALT_NAME_PATTERN = re.compile(r'Alternative name\s+"([^"]+)"', re.IGNORECASE)


@dataclass(slots=True)
class _DShowDeviceRecord:
    name: str
    alternative_name: str = ""


def _extract_vid_pid(*parts: str) -> str:
    """Extract ``VID_XXXX&PID_YYYY`` from DirectShow alternative names."""

    for part in parts:
        if not part:
            continue
        match = _VID_PID_PATTERN.search(part)
        if match:
            return f"VID_{match.group(1).upper()}&PID_{match.group(2).upper()}"
    return ""


def _is_recommended_device(name: str, alternative_name: str, vid_pid: str) -> bool:
    if name == DEFAULT_CAMERA_NAME or "LRCP" in name.upper():
        return True
    if vid_pid == DEFAULT_VID_PID:
        return True
    combined = f"{name} {alternative_name}".lower()
    return DEFAULT_VID_PID_TOKEN in combined


def _run_ffmpeg_list_devices() -> tuple[bool, str]:
    """Run FFmpeg DirectShow device listing and return stderr/stdout text."""

    if sys.platform != "win32":
        return False, ""
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
        return False, ""

    text = (completed.stderr or "") + (completed.stdout or "")
    return True, text


def _parse_ffmpeg_dshow_devices(text: str) -> list[_DShowDeviceRecord]:
    """Parse FFmpeg DirectShow listing into video device records."""

    records: list[_DShowDeviceRecord] = []
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
        if not stripped:
            continue

        if "Alternative name" in stripped:
            if records:
                alt_match = _ALT_NAME_PATTERN.search(stripped)
                if alt_match:
                    records[-1].alternative_name = alt_match.group(1)
                else:
                    alt_value = stripped.split("Alternative name", 1)[-1].strip().strip('"')
                    if alt_value:
                        records[-1].alternative_name = alt_value
            continue

        name_match = re.search(r'"([^"]+)"', stripped)
        if name_match and "Alternative name" not in stripped:
            records.append(_DShowDeviceRecord(name=name_match.group(1)))

    return records


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


def _build_camera_info(
    *,
    index: int,
    name: str,
    alternative_name: str = "",
    names_from_ffmpeg: bool,
) -> CameraInfo:
    vid_pid = _extract_vid_pid(alternative_name, name)
    recommended = _is_recommended_device(name, alternative_name, vid_pid)
    return CameraInfo(
        index=index,
        name=name,
        alternative_name=alternative_name,
        vid_pid=vid_pid,
        recommended=recommended,
        names_from_ffmpeg=names_from_ffmpeg,
    )


def _merge_ffmpeg_with_indices(
    records: Iterable[_DShowDeviceRecord],
    indices: Iterable[int],
) -> list[CameraInfo]:
    record_list = list(records)
    index_list = list(indices)
    if not record_list and not index_list:
        return []

    if record_list and not index_list:
        index_list = list(range(len(record_list)))

    devices: list[CameraInfo] = []
    for position, index in enumerate(index_list):
        if position < len(record_list):
            record = record_list[position]
            devices.append(
                _build_camera_info(
                    index=index,
                    name=record.name,
                    alternative_name=record.alternative_name,
                    names_from_ffmpeg=True,
                )
            )
        else:
            devices.append(
                _build_camera_info(
                    index=index,
                    name=f"Camera {index}",
                    names_from_ffmpeg=False,
                )
            )
    return devices


def _enumerate_opencv_fallback(*, max_index: int) -> list[CameraInfo]:
    indices = _probe_opencv_indices(max_index=max_index)
    return [
        _build_camera_info(
            index=index,
            name=f"Camera {index}",
            names_from_ffmpeg=False,
        )
        for index in indices
    ]


def enumerate_cameras(*, max_index: int = 10) -> CameraEnumerationResult:
    """Enumerate local cameras without keeping any device open."""

    if sys.platform != "win32":
        return CameraEnumerationResult(devices=[], ffmpeg_available=False, used_ffmpeg_names=False)

    ffmpeg_available, ffmpeg_text = _run_ffmpeg_list_devices()
    records = _parse_ffmpeg_dshow_devices(ffmpeg_text) if ffmpeg_available and ffmpeg_text else []
    indices = _probe_opencv_indices(max_index=max_index)

    if records:
        devices = _merge_ffmpeg_with_indices(records, indices)
        if devices:
            return CameraEnumerationResult(
                devices=devices,
                ffmpeg_available=ffmpeg_available,
                used_ffmpeg_names=True,
            )

    fallback_devices = _enumerate_opencv_fallback(max_index=max_index)
    if fallback_devices:
        return CameraEnumerationResult(
            devices=fallback_devices,
            ffmpeg_available=ffmpeg_available,
            used_ffmpeg_names=False,
        )

    if records:
        devices = [
            _build_camera_info(
                index=position,
                name=record.name,
                alternative_name=record.alternative_name,
                names_from_ffmpeg=True,
            )
            for position, record in enumerate(records)
        ]
        return CameraEnumerationResult(
            devices=devices,
            ffmpeg_available=ffmpeg_available,
            used_ffmpeg_names=True,
        )

    return CameraEnumerationResult(
        devices=[
            _build_camera_info(
                index=0,
                name=DEFAULT_CAMERA_NAME,
                names_from_ffmpeg=False,
            )
        ],
        ffmpeg_available=ffmpeg_available,
        used_ffmpeg_names=False,
    )


def find_default_camera(devices: list[CameraInfo]) -> CameraInfo | None:
    """Return the preferred LRCP / VID_1BCF&PID_2CC8 device when present."""

    for device in devices:
        if device.recommended:
            return device
    for device in devices:
        if device.name == DEFAULT_CAMERA_NAME:
            return device
        if "LRCP" in device.name.upper():
            return device
        if device.vid_pid == DEFAULT_VID_PID:
            return device
        if DEFAULT_VID_PID_TOKEN in device.alternative_name.lower():
            return device
    return devices[0] if devices else None
