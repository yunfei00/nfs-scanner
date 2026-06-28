"""Background worker that streams camera frames without blocking the UI."""

from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from .opencv_camera import OpenCVCameraDevice
from .qt_image import bgr_frame_to_qimage

logger = logging.getLogger(__name__)


class CameraWorker(QThread):
    """Poll camera frames on a worker thread and emit ``QImage`` previews."""

    frame_ready = Signal(QImage)
    error_occurred = Signal(str)

    def __init__(self, device: OpenCVCameraDevice, *, interval_ms: int = 33, parent=None) -> None:
        super().__init__(parent)
        self._device = device
        self._interval_ms = max(1, interval_ms)
        self._running = False

    def run(self) -> None:
        """Continuously read frames until ``stop()`` is requested."""

        self._running = True
        self._device.mark_previewing(True)
        while self._running:
            try:
                frame = self._device.read_frame()
            except Exception as exc:  # pragma: no cover - hardware dependent
                logger.exception("Camera worker read failed")
                self.error_occurred.emit(str(exc))
                break
            if frame is None:
                if self._device.last_error:
                    self.error_occurred.emit(self._device.last_error)
                    break
                self.msleep(self._interval_ms)
                continue
            image = bgr_frame_to_qimage(frame)
            if not image.isNull():
                self.frame_ready.emit(image)
            self.msleep(self._interval_ms)
        self._device.mark_previewing(False)

    def stop(self) -> None:
        """Request the worker loop to exit and wait briefly."""

        self._running = False
        if self.isRunning():
            self.wait(3000)
