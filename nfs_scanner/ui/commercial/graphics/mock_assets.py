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
    """Generate a PCB-like placeholder board image for PhotoLayer."""

    base = np.zeros((height, width, 3), dtype=np.uint8)
    base[:, :] = (11, 18, 15)

    board_x, board_y, board_w, board_h = board_content_rect(width, height)
    left = int(board_x)
    top = int(board_y)
    right = int(board_x + board_w)
    bottom = int(board_y + board_h)

    board = base[top:bottom, left:right]
    board[:, :] = (26, 58, 42)

    _draw_pcb_traces(board, seed=11)
    _draw_pcb_chips(board, seed=17)
    _draw_pcb_vias(board, seed=23)
    _draw_pcb_connector(board)

    base[top:bottom, left:right] = board
    return _array_to_qimage(base)


def _draw_pcb_traces(board: NDArray[np.uint8], *, seed: int) -> None:
    height, width = board.shape[:2]
    rng = np.random.default_rng(seed)
    trace_color = np.array([48, 92, 68], dtype=np.uint8)
    for _ in range(18):
        x = int(rng.integers(8, width - 8))
        y = int(rng.integers(8, height - 8))
        length = int(rng.integers(24, min(width, height) // 2))
        horizontal = rng.random() > 0.5
        if horizontal:
            x_end = min(x + length, width - 2)
            board[y : y + 2, x:x_end] = trace_color
        else:
            y_end = min(y + length, height - 2)
            board[y:y_end, x : x + 2] = trace_color


def _draw_pcb_chips(board: NDArray[np.uint8], *, seed: int) -> None:
    height, width = board.shape[:2]
    rng = np.random.default_rng(seed)
    chip_body = np.array([18, 28, 22], dtype=np.uint8)
    chip_pin = np.array([72, 88, 78], dtype=np.uint8)
    placements = (
        (0.12, 0.14, 0.22, 0.16),
        (0.38, 0.10, 0.28, 0.20),
        (0.62, 0.18, 0.24, 0.18),
        (0.18, 0.48, 0.30, 0.22),
        (0.55, 0.52, 0.26, 0.24),
    )
    for px, py, pw, ph in placements:
        x0 = int(px * width)
        y0 = int(py * height)
        x1 = min(int((px + pw) * width), width - 2)
        y1 = min(int((py + ph) * height), height - 2)
        board[y0:y1, x0:x1] = chip_body
        board[y0 - 2 : y0, x0:x1:4] = chip_pin
        board[y1 : y1 + 2, x0:x1:4] = chip_pin
        board[y0:y1:4, x0 - 2 : x0] = chip_pin
        board[y0:y1:4, x1 : x1 + 2] = chip_pin
        label_x = x0 + (x1 - x0) // 3
        label_y = y0 + (y1 - y0) // 3
        board[label_y : label_y + 4, label_x : label_x + 8] = (12, 18, 14)


def _draw_pcb_vias(board: NDArray[np.uint8], *, seed: int) -> None:
    height, width = board.shape[:2]
    rng = np.random.default_rng(seed)
    via_color = np.array([120, 132, 118], dtype=np.uint8)
    for _ in range(28):
        cx = int(rng.integers(6, width - 6))
        cy = int(rng.integers(6, height - 6))
        board[cy - 1 : cy + 2, cx - 1 : cx + 2] = via_color


def _draw_pcb_connector(board: NDArray[np.uint8]) -> None:
    height, width = board.shape[:2]
    x0 = int(width * 0.04)
    y0 = int(height * 0.72)
    x1 = int(width * 0.18)
    y1 = int(height * 0.92)
    board[y0:y1, x0:x1] = (14, 22, 18)
    for row in range(y0 + 4, y1 - 4, 6):
        board[row : row + 3, x0 + 4 : x1 - 4 : 5] = (180, 186, 176)


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
    """Generate one smooth RGBA heatmap image aligned to the board dimensions."""

    board_x, board_y, board_w, board_h = board_content_rect(width, height)
    field = _create_smooth_field(width, height, seed=seed)

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
    field[outside_board] *= 0.08

    rgb = _apply_spectral_lut(field)
    alpha = np.full((height, width), 165, dtype=np.uint8)
    alpha[outside_board] = 24
    rgba = np.dstack((rgb, alpha))
    return _array_to_qimage(rgba, rgba=True)


def _create_smooth_field(width: int, height: int, *, seed: int) -> NDArray[np.float64]:
    """Build a blurred multi-hotspot scalar field for heatmap rendering."""

    rng = np.random.default_rng(seed)
    y_coords, x_coords = np.mgrid[0:height, 0:width]
    field = np.zeros((height, width), dtype=np.float64)

    board_x, board_y, board_w, board_h = board_content_rect(width, height)
    hotspots = (
        (board_x + board_w * 0.35, board_y + board_h * 0.42, 90.0, 1.0),
        (board_x + board_w * 0.62, board_y + board_h * 0.28, 70.0, 0.85),
        (board_x + board_w * 0.48, board_y + board_h * 0.68, 110.0, 0.75),
        (board_x + board_w * 0.22, board_y + board_h * 0.55, 60.0, 0.55),
    )
    for cx, cy, sigma, weight in hotspots:
        field += weight * np.exp(-((x_coords - cx) ** 2 + (y_coords - cy) ** 2) / (2 * sigma**2))

    field += 0.04 * rng.random((height, width))
    for _ in range(4):
        field = _box_blur(field, kernel=7)
    field -= field.min()
    maximum = field.max()
    if maximum > 0:
        field /= maximum
    return field


def _box_blur(values: NDArray[np.float64], *, kernel: int) -> NDArray[np.float64]:
    """Apply a simple separable box blur without extra dependencies."""

    pad = kernel // 2
    kernel_1d = np.ones(kernel, dtype=np.float64) / kernel
    padded_h = np.pad(values, ((0, 0), (pad, pad)), mode="edge")
    temp = np.empty_like(values)
    for row in range(values.shape[0]):
        temp[row] = np.convolve(padded_h[row], kernel_1d, mode="valid")
    padded_v = np.pad(temp, ((pad, pad), (0, 0)), mode="edge")
    blurred = np.empty_like(values)
    for col in range(values.shape[1]):
        blurred[:, col] = np.convolve(padded_v[:, col], kernel_1d, mode="valid")
    return blurred


def _apply_spectral_lut(values: NDArray[np.float64]) -> NDArray[np.uint8]:
    """Map normalized values to a blue-green-yellow-red LUT."""

    scaled = values * 4.0
    red = np.clip(1.5 - np.abs(scaled - 3.0), 0.0, 1.0)
    green = np.clip(1.5 - np.abs(scaled - 2.0), 0.0, 1.0)
    blue = np.clip(1.5 - np.abs(scaled - 1.0), 0.0, 1.0)
    rgb = np.dstack(
        (
            (red * 255.0).astype(np.uint8),
            (green * 255.0).astype(np.uint8),
            (blue * 255.0).astype(np.uint8),
        )
    )
    return rgb


def _array_to_qimage(array: NDArray[np.uint8], *, rgba: bool = False) -> QImage:
    """Convert a numpy RGB/RGBA array into a QImage."""

    height, width = array.shape[:2]
    if rgba:
        image = QImage(array.data, width, height, width * 4, QImage.Format.Format_RGBA8888)
    else:
        image = QImage(array.data, width, height, width * 3, QImage.Format.Format_RGB888)
    return image.copy()
