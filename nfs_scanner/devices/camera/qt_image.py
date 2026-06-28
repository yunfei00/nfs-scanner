"""Convert OpenCV BGR frames to ``QImage``."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from PySide6.QtGui import QImage


def bgr_frame_to_qimage(frame: NDArray[np.uint8]) -> QImage:
    """Convert one OpenCV BGR ``uint8`` frame into an RGB ``QImage``."""

    if frame.ndim == 2:
        height, width = frame.shape
        bytes_per_line = width
        return QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8).copy()

    if frame.ndim != 3 or frame.shape[2] < 3:
        return QImage()

    rgb = np.ascontiguousarray(frame[:, :, ::-1])
    height, width, _channels = rgb.shape
    bytes_per_line = 3 * width
    return QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).copy()
