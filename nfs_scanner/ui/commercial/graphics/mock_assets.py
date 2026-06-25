"""Mock image helpers for commercial graphics layers."""

from __future__ import annotations

import numpy as np
from PySide6.QtGui import QImage
from numpy.typing import NDArray

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
BOARD_INSET_RATIO = 0.12


def board_content_rect(
    width: int = CANVAS_WIDTH,
    height: int = CANVAS_HEIGHT,
) -> tuple[float, float, float, float]:
    """Return the active board area inset within the canvas."""

    inset_x = width * BOARD_INSET_RATIO
    inset_y = height * BOARD_INSET_RATIO
    return inset_x, inset_y, width - (2 * inset_x), height - (2 * inset_y)


def create_mock_board_qimage(width: int = CANVAS_WIDTH, height: int = CANVAS_HEIGHT) -> QImage:
    """Generate a placeholder board image for PhotoLayer."""

    y_coords, x_coords = np.mgrid[0:height, 0:width]
    base = np.full((height, width, 3), 28, dtype=np.uint8)
    base[:, :, 1] = 42
    base[:, :, 2] = 36

    grid_mask = ((x_coords % 40) < 2) | ((y_coords % 40) < 2)
    base[grid_mask] = (18, 28, 24)

    board_x, board_y, board_w, board_h = board_content_rect(width, height)
    board_left = int(board_x)
    board_top = int(board_y)
    board_right = int(board_x + board_w)
    board_bottom = int(board_y + board_h)

    board_mask = (
        (x_coords >= board_left)
        & (x_coords < board_right)
        & (y_coords >= board_top)
        & (y_coords < board_bottom)
    )
    base[board_mask] = (52, 72, 64)

    center_x = int(board_x + board_w / 2)
    center_y = int(board_y + board_h / 2)
    marker_radius = max(int(min(board_w, board_h) * 0.04), 8)
    center_mask = (x_coords - center_x) ** 2 + (y_coords - center_y) ** 2 <= marker_radius**2
    base[center_mask] = (72, 96, 84)

    return _array_to_qimage(base)


def generate_snake_path_points(
    *,
    width: int = CANVAS_WIDTH,
    height: int = CANVAS_HEIGHT,
    cols: int = 14,
    rows: int = 10,
) -> list[tuple[float, float]]:
    """Generate a snake scan path covering the mock board area."""

    board_x, board_y, board_w, board_h = board_content_rect(width, height)
    step_x = board_w / max(cols - 1, 1)
    step_y = board_h / max(rows - 1, 1)

    points: list[tuple[float, float]] = []
    for row in range(rows):
        x_values = range(cols) if row % 2 == 0 else range(cols - 1, -1, -1)
        for col in x_values:
            points.append((board_x + col * step_x, board_y + row * step_y))
    return points


def create_mock_heatmap_qimage(
    width: int = CANVAS_WIDTH,
    height: int = CANVAS_HEIGHT,
    *,
    seed: int = 20260625,
) -> QImage:
    """Generate one RGBA heatmap image aligned to the board dimensions."""

    rng = np.random.default_rng(seed)
    matrix = rng.random((height, width), dtype=np.float64)

    board_x, board_y, board_w, board_h = board_content_rect(width, height)
    board_left = int(board_x)
    board_top = int(board_y)
    board_right = int(board_x + board_w)
    board_bottom = int(board_y + board_h)

    y_coords, x_coords = np.mgrid[0:height, 0:width]
    outside_board = (
        (x_coords < board_left)
        | (x_coords >= board_right)
        | (y_coords < board_top)
        | (y_coords >= board_bottom)
    )
    matrix[outside_board] *= 0.15

    matrix = _apply_lut(matrix)
    alpha = np.full((height, width), 180, dtype=np.uint8)
    alpha[outside_board] = 40
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
