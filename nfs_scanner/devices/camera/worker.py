"""Background worker that streams camera frames without blocking the UI."""

from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal

from .opencv_camera import OpenCVCameraDevice

logger = logging.getLogger(__name__)


class CameraWorker(QThread):
    """Poll camera frames on a worker thread and emit raw BGR frames."""

    frame_ready = Signal(object)
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
            self.frame_ready.emit(frame.copy())
            self.msleep(self._interval_ms)
        self._device.mark_previewing(False)

    def stop(self) -> None:
        """Request the worker loop to exit and wait briefly."""

        self._running = False
        if self.isRunning():
            self.wait(3000)
