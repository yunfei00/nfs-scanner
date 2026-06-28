"""OpenCV DirectShow camera device implementation."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .base_camera import CameraDevice
from .models import CameraProfile, CameraState
from ._opencv_import import require_opencv

logger = logging.getLogger(__name__)


class OpenCVCameraDevice(CameraDevice):
    """USB UVC camera accessed through OpenCV DirectShow backend on Windows."""

    def __init__(
        self,
        device_index: int,
        profile: CameraProfile,
        *,
        device_name: str = "",
    ) -> None:
        self._device_index = device_index
        self._profile = profile
        self._device_name = device_name
        self._capture: Any | None = None
        self._state = CameraState.DISCONNECTED
        self._last_error = ""

    @property
    def device_index(self) -> int:
        return self._device_index

    @property
    def device_name(self) -> str:
        return self._device_name

    @property
    def profile(self) -> CameraProfile:
        return self._profile

    @property
    def state(self) -> CameraState:
        return self._state

    @property
    def last_error(self) -> str:
        return self._last_error

    def connect(self) -> bool:
        """Open the camera with the configured DirectShow profile."""

        if self._capture is not None and self._capture.isOpened():
            self._state = CameraState.CONNECTED
            return True

        cv2 = require_opencv()
        if cv2 is None:  # pragma: no cover - guarded by require_opencv
            self._set_error("OpenCV 未安装")
            return False

        capture = cv2.VideoCapture(self._device_index, cv2.CAP_DSHOW)
        if not capture.isOpened():
            capture.release()
            self._set_error(f"无法打开相机索引 {self._device_index}")
            return False

        fourcc = self._profile.fourcc[:4].ljust(4, " ")
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(self._profile.width))
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self._profile.height))
        capture.set(cv2.CAP_PROP_FPS, float(self._profile.fps))

        self._capture = capture
        self._state = CameraState.CONNECTED
        self._last_error = ""
        logger.info(
            "Camera opened index=%s name=%r profile=%s",
            self._device_index,
            self._device_name,
            self._profile.resolution_label,
        )
        return True

    def disconnect(self) -> None:
        """Release the underlying ``VideoCapture`` handle."""

        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._state = CameraState.DISCONNECTED
        self._last_error = ""

    def read_frame(self) -> NDArray[np.uint8] | None:
        """Read one BGR frame from the device."""

        self._ensure_open()
        assert self._capture is not None
        ok, frame = self._capture.read()
        if not ok or frame is None:
            self._set_error("读取相机帧失败")
            return None
        return np.asarray(frame, dtype=np.uint8)

    def capture_image(self) -> NDArray[np.uint8]:
        """Capture one frame and raise when the read fails."""

        frame = self.read_frame()
        if frame is None:
            raise RuntimeError(self._last_error or "Camera frame capture failed.")
        return frame

    def mark_previewing(self, active: bool) -> None:
        """Update preview state without touching the capture handle."""

        if self._capture is None or not self._capture.isOpened():
            self._state = CameraState.DISCONNECTED
            return
        self._state = CameraState.PREVIEWING if active else CameraState.CONNECTED

    def _ensure_open(self) -> None:
        if self._capture is None or not self._capture.isOpened():
            raise RuntimeError("Camera device is not connected.")

    def _set_error(self, message: str) -> None:
        self._last_error = message
        self._state = CameraState.ERROR
        logger.warning("Camera error: %s", message)
