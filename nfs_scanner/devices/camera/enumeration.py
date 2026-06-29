"""Camera enumeration helpers for Windows DirectShow / OpenCV."""

from __future__ import annotations

import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable

from .constants import (
    CAMERA_SAFE_ENUMERATION,
    DEFAULT_CAMERA_NAME,
    DEFAULT_VID_PID,
    DEFAULT_VID_PID_TOKEN,
    is_opencv_probe_allowed,
)
from .models import CameraEnumerationResult, CameraInfo
from ._opencv_import import opencv_available, require_opencv

logger = logging.getLogger(__name__)

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


def _list_pnp_cameras_via_powershell() -> list[_DShowDeviceRecord]:
    """List camera-class PnP devices without opening any capture handle."""

    if sys.platform != "win32":
        return []
    command = (
        "Get-CimInstance Win32_PnPEntity | "
        "Where-Object { $_.PNPClass -in @('Camera','Image') } | "
        "ForEach-Object { \"$($_.Name)|$($_.PNPDeviceID)\" }"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []

    records: list[_DShowDeviceRecord] = []
    for line in (completed.stdout or "").splitlines():
        stripped = line.strip()
        if not stripped or "|" not in stripped:
            continue
        name, pnp_id = stripped.split("|", 1)
        if name:
            records.append(_DShowDeviceRecord(name=name.strip(), alternative_name=pnp_id.strip()))
    return records


def _probe_opencv_indices(max_index: int = 10) -> list[int]:
    """Probe DirectShow indices that OpenCV can open (dev/debug only)."""

    if not is_opencv_probe_allowed():
        logger.debug("Skipping OpenCV camera index probe (safe enumeration enabled)")
        return []
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


def _devices_from_records(
    records: Iterable[_DShowDeviceRecord],
    *,
    names_from_ffmpeg: bool,
    indices: Iterable[int] | None = None,
) -> list[CameraInfo]:
    record_list = list(records)
    if not record_list:
        return []

    index_list = list(indices) if indices is not None else list(range(len(record_list)))
    if not index_list:
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
                    names_from_ffmpeg=names_from_ffmpeg,
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


def _placeholder_devices(*, max_index: int) -> list[CameraInfo]:
    """Return unverified index placeholders without opening hardware."""

    known_names = ("Integrated Webcam", DEFAULT_CAMERA_NAME)
    count = max(1, min(max_index, len(known_names)))
    devices: list[CameraInfo] = []
    for index in range(count):
        name = known_names[index] if index < len(known_names) else f"Camera {index}"
        devices.append(
            _build_camera_info(index=index, name=name, names_from_ffmpeg=False),
        )
    return devices


def enumerate_cameras(*, max_index: int = 10) -> CameraEnumerationResult:
    """Enumerate local cameras without opening any capture device."""

    if sys.platform != "win32":
        return CameraEnumerationResult(devices=[], ffmpeg_available=False, used_ffmpeg_names=False)

    ffmpeg_available, ffmpeg_text = _run_ffmpeg_list_devices()
    records = _parse_ffmpeg_dshow_devices(ffmpeg_text) if ffmpeg_available and ffmpeg_text else []

    indices: list[int] = []
    if is_opencv_probe_allowed():
        indices = _probe_opencv_indices(max_index=max_index)

    if records:
        devices = _devices_from_records(
            records,
            names_from_ffmpeg=True,
            indices=indices if indices else None,
        )
        return CameraEnumerationResult(
            devices=devices,
            ffmpeg_available=ffmpeg_available,
            used_ffmpeg_names=True,
        )

    pnp_records = _list_pnp_cameras_via_powershell()
    if pnp_records:
        devices = _devices_from_records(
            pnp_records,
            names_from_ffmpeg=False,
            indices=indices if indices else None,
        )
        return CameraEnumerationResult(
            devices=devices,
            ffmpeg_available=ffmpeg_available,
            used_ffmpeg_names=False,
        )

    if indices and is_opencv_probe_allowed():
        devices = [
            _build_camera_info(index=index, name=f"Camera {index}", names_from_ffmpeg=False)
            for index in indices
        ]
        return CameraEnumerationResult(
            devices=devices,
            ffmpeg_available=ffmpeg_available,
            used_ffmpeg_names=False,
        )

    if CAMERA_SAFE_ENUMERATION:
        return CameraEnumerationResult(
            devices=_placeholder_devices(max_index=min(max_index, 2)),
            ffmpeg_available=ffmpeg_available,
            used_ffmpeg_names=False,
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
