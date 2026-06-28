"""High-level camera manager for preview and snapshot workflows."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PySide6.QtGui import QImage

from .constants import DEFAULT_FPS, DEFAULT_FOURCC, DEFAULT_HEIGHT, DEFAULT_WIDTH, SNAPSHOT_DIR_NAME
from .enumeration import enumerate_cameras, find_default_camera
from .models import CameraInfo, CameraProfile, CameraState
from .opencv_camera import OpenCVCameraDevice
from .qt_image import bgr_frame_to_qimage
from .worker import CameraWorker
from ._opencv_import import opencv_available, require_opencv

logger = logging.getLogger(__name__)


class CameraManager:
    """Manage one active USB camera, preview worker, and snapshot output."""

    def __init__(self, *, output_dir: Path | None = None) -> None:
        self._output_dir = output_dir or Path(SNAPSHOT_DIR_NAME)
        self._device: OpenCVCameraDevice | None = None
        self._worker: CameraWorker | None = None
        self._state = CameraState.DISCONNECTED
        self._last_error = ""
        self._last_frame: NDArray[np.uint8] | None = None
        self._last_qimage = QImage()

    @property
    def state(self) -> CameraState:
        if self._device is not None and self._device.state != CameraState.DISCONNECTED:
            return self._device.state
        return self._state

    @property
    def last_error(self) -> str:
        if self._device is not None and self._device.last_error:
            return self._device.last_error
        return self._last_error

    @property
    def output_dir(self) -> Path:
        return self._output_dir

    @property
    def last_qimage(self) -> QImage:
        return self._last_qimage

    @staticmethod
    def is_supported() -> bool:
        """Return True when OpenCV camera capture is available on this platform."""

        return opencv_available()

    def list_devices(self) -> list[CameraInfo]:
        """Enumerate cameras without opening them."""

        return enumerate_cameras()

    def default_device(self) -> CameraInfo | None:
        """Return the preferred default camera when available."""

        return find_default_camera(self.list_devices())

    def open(self, device: CameraInfo, profile: CameraProfile | None = None) -> bool:
        """Open the selected camera using the given profile."""

        self.close()
        selected_profile = profile or CameraProfile(
            width=DEFAULT_WIDTH,
            height=DEFAULT_HEIGHT,
            fps=DEFAULT_FPS,
            fourcc=DEFAULT_FOURCC,
        )
        self._device = OpenCVCameraDevice(
            device_index=device.index,
            profile=selected_profile,
            device_name=device.name,
        )
        if not self._device.connect():
            self._last_error = self._device.last_error
            self._state = CameraState.ERROR
            self._device = None
            return False
        self._state = CameraState.CONNECTED
        self._last_error = ""
        return True

    def close(self) -> None:
        """Stop preview and release the active camera."""

        self.stop_preview()
        if self._device is not None:
            self._device.disconnect()
            self._device = None
        self._state = CameraState.DISCONNECTED
        self._last_error = ""

    def start_preview(self) -> CameraWorker | None:
        """Start background preview streaming; caller should connect worker signals."""

        if self._device is None:
            self._last_error = "相机未打开"
            self._state = CameraState.ERROR
            return None
        if self._worker is not None and self._worker.isRunning():
            return self._worker

        worker = CameraWorker(self._device, interval_ms=max(1, 1000 // max(1, self._device.profile.fps)))
        self._worker = worker
        worker.start()
        self._state = CameraState.PREVIEWING
        return worker

    def stop_preview(self) -> None:
        """Stop the preview worker without necessarily closing the device."""

        if self._worker is not None:
            self._worker.stop()
            self._worker = None
        if self._device is not None and self._device.state == CameraState.PREVIEWING:
            self._device.mark_previewing(False)
            self._state = CameraState.CONNECTED
        elif self._device is None:
            self._state = CameraState.DISCONNECTED

    def read_frame(self) -> NDArray[np.uint8] | None:
        """Read one frame from the active device."""

        if self._device is None:
            return None
        try:
            frame = self._device.read_frame()
        except Exception as exc:  # pragma: no cover - hardware dependent
            self._last_error = str(exc)
            self._state = CameraState.ERROR
            return None
        if frame is not None:
            self._remember_frame(frame)
        return frame

    def capture_snapshot(self, *, output_dir: Path | None = None) -> Path | None:
        """Capture one frame and save it as a JPEG under ``outputs/camera/``."""

        frame = self.read_frame()
        if frame is None:
            if self._last_frame is not None:
                frame = self._last_frame.copy()
            else:
                self._last_error = self._last_error or "没有可用帧，无法拍照"
                return None

        target_dir = output_dir or self._output_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = target_dir / f"camera_{timestamp}.jpg"

        cv2 = require_opencv()
        ok = cv2.imwrite(str(target_path), frame)
        if not ok:
            self._last_error = f"保存图片失败: {target_path}"
            return None
        logger.info("Camera snapshot saved: %s", target_path)
        return target_path

    def remember_qimage(self, image: QImage) -> None:
        """Store the latest preview frame for snapshot fallback."""

        if not image.isNull():
            self._last_qimage = image.copy()

    def _remember_frame(self, frame: NDArray[np.uint8]) -> None:
        self._last_frame = frame
        image = bgr_frame_to_qimage(frame)
        if not image.isNull():
            self._last_qimage = image
