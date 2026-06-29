"""Default camera parameters for the LRCP  F1080P UVC device."""

from __future__ import annotations

import os

# Device friendly name from Windows DirectShow / FFmpeg listing.
# IMPORTANT: keep the double space between LRCP and F1080P.
DEFAULT_CAMERA_NAME = "LRCP  F1080P"

DEFAULT_HARDWARE_ID = r"USB\VID_1BCF&PID_2CC8&MI_00"
DEFAULT_VID_PID = "VID_1BCF&PID_2CC8"
DEFAULT_VID_PID_TOKEN = "vid_1bcf&pid_2cc8"

DEFAULT_FOURCC = "MJPG"
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_FPS = 30

# When True (default), device enumeration must not open cameras via OpenCV.
CAMERA_SAFE_ENUMERATION = True

# Explicit env opt-in required to probe indices with cv2.VideoCapture during enumeration.
CAMERA_PROBE_ENV_VAR = "NFS_SCANNER_CAMERA_PROBE"

# MJPEG-friendly resolution presets (width, height).
MJPEG_RESOLUTIONS: tuple[tuple[int, int], ...] = (
    (1920, 1080),
    (1280, 720),
    (1280, 960),
    (800, 600),
    (640, 480),
    (320, 240),
)

FPS_OPTIONS: tuple[int, ...] = (5, 10, 15, 20, 25, 30)

SNAPSHOT_DIR_NAME = "outputs/camera"


def is_opencv_probe_allowed() -> bool:
    """Return True only when OpenCV index probing is explicitly allowed."""

    probe_enabled = os.getenv(CAMERA_PROBE_ENV_VAR, "").strip().lower() in ("1", "true", "yes", "on")
    if probe_enabled:
        return True
    return not CAMERA_SAFE_ENUMERATION
