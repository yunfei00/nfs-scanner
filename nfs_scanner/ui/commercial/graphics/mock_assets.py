"""Mock image helpers for commercial graphics layers."""

from __future__ import annotations

import numpy as np
from PySide6.QtGui import QImage
from numpy.typing import NDArray

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600


def create_mock_board_qimage(width: int = CANVAS_WIDTH, height: int = CANVAS_HEIGHT) -> QImage:
    """Generate a placeholder board image for PhotoLayer."""

    y_coords, x_coords = np.mgrid[0:height, 0:width]
    base = np.full((height, width, 3), 28, dtype=np.uint8)
    base[:, :, 1] = 42
    base[:, :, 2] = 36

    grid_mask = ((x_coords % 40) < 2) | ((y_coords % 40) < 2)
    base[grid_mask] = (18, 28, 24)

    center_x = width // 2
    center_y = height // 2
    radius = min(width, height) // 5
    board_mask = (x_coords - center_x) ** 2 + (y_coords - center_y) ** 2 <= radius**2
    base[board_mask] = (52, 72, 64)

    return _array_to_qimage(base)


def create_mock_heatmap_qimage(
    width: int = CANVAS_WIDTH,
    height: int = CANVAS_HEIGHT,
    *,
    seed: int = 20260625,
) -> QImage:
    """Generate one RGBA heatmap image aligned to the board dimensions."""

    rng = np.random.default_rng(seed)
    matrix = rng.random((height, width), dtype=np.float64)
    matrix = _apply_lut(matrix)
    alpha = np.full((height, width), 180, dtype=np.uint8)
    rgba = np.dstack((matrix, alpha))
    return _array_to_qimage(rgba, rgba=True)


def _apply_lut(values: NDArray[np.float64]) -> NDArray[np.uint8]:
    """Map normalized values to a simple blue-cyan-yellow LUT."""

    red = np.clip(values * 255.0, 0, 255).astype(np.uint8)
    green = np.clip((values**0.7) * 255.0, 0, 255).astype(np.uint8)
    blue = np.clip((1.0 - values) * 255.0, 0, 255).astype(np.uint8)
    return np.dstack((red, green, blue))


def _array_to_qimage(array: NDArray[np.uint8], *, rgba: bool = False) -> QImage:
    """Convert a numpy RGB/RGBA array into a QImage."""

    height, width = array.shape[:2]
    if rgba:
        image = QImage(array.data, width, height, width * 4, QImage.Format.Format_RGBA8888)
    else:
        image = QImage(array.data, width, height, width * 3, QImage.Format.Format_RGB888)
    return image.copy()
