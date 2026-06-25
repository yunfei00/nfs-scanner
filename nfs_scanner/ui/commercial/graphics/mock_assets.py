"""Mock image helpers for commercial graphics layers."""

from __future__ import annotations

import numpy as np
from PySide6.QtGui import QImage
from numpy.typing import NDArray

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
BOARD_INSET_RATIO = 0.03


def board_content_rect(
    width: int = CANVAS_WIDTH,
    height: int = CANVAS_HEIGHT,
) -> tuple[float, float, float, float]:
    """Return the active board area inset within the canvas."""

    inset_x = width * BOARD_INSET_RATIO
    inset_y = height * BOARD_INSET_RATIO
    return inset_x, inset_y, width - (2 * inset_x), height - (2 * inset_y)


def create_mock_board_qimage(width: int = CANVAS_WIDTH, height: int = CANVAS_HEIGHT) -> QImage:
    """Generate a realistic PCB mock image filling most of the canvas."""

    base = np.zeros((height, width, 3), dtype=np.uint8)
    base[:, :] = (22, 38, 32)

    board_x, board_y, board_w, board_h = board_content_rect(width, height)
    left = int(board_x)
    top = int(board_y)
    right = int(board_x + board_w)
    bottom = int(board_y + board_h)

    board = base[top:bottom, left:right].copy()
    board[:, :] = (32, 72, 52)

    _draw_pcb_silkscreen(board)
    _draw_pcb_traces(board, seed=11)
    _draw_pcb_chips(board, seed=17)
    _draw_pcb_vias(board, seed=23)
    _draw_pcb_connector(board)
    _draw_pcb_usb(board)
    _apply_board_shadow(board)

    base[top:bottom, left:right] = board
    return _array_to_qimage(base)


def _draw_pcb_silkscreen(board: NDArray[np.uint8]) -> None:
    height, width = board.shape[:2]
    silk = np.array([58, 78, 66], dtype=np.uint8)
    board[8 : height - 8 : 48, 8:width - 8 : 3] = silk


def _draw_pcb_traces(board: NDArray[np.uint8], *, seed: int) -> None:
    height, width = board.shape[:2]
    rng = np.random.default_rng(seed)
    trace_color = np.array([56, 108, 78], dtype=np.uint8)
    for _ in range(36):
        x = int(rng.integers(10, width - 10))
        y = int(rng.integers(10, height - 10))
        length = int(rng.integers(30, min(width, height) // 2))
        thickness = 2 if rng.random() > 0.3 else 3
        horizontal = rng.random() > 0.45
        if horizontal:
            x_end = min(x + length, width - 2)
            board[y : y + thickness, x:x_end] = trace_color
        else:
            y_end = min(y + length, height - 2)
            board[y:y_end, x : x + thickness] = trace_color


def _draw_pcb_chips(board: NDArray[np.uint8], *, seed: int) -> None:
    height, width = board.shape[:2]
    chip_body = np.array([16, 24, 20], dtype=np.uint8)
    chip_pin = np.array([168, 178, 162], dtype=np.uint8)
    chip_shadow = np.array([12, 18, 14], dtype=np.uint8)
    placements = (
        (0.10, 0.12, 0.24, 0.18),
        (0.36, 0.08, 0.30, 0.22),
        (0.58, 0.14, 0.28, 0.20),
        (0.14, 0.44, 0.32, 0.24),
        (0.50, 0.48, 0.30, 0.26),
        (0.72, 0.52, 0.18, 0.16),
    )
    for px, py, pw, ph in placements:
        x0 = int(px * width)
        y0 = int(py * height)
        x1 = min(int((px + pw) * width), width - 3)
        y1 = min(int((py + ph) * height), height - 3)
        board[y1 : y1 + 2, x0:x1] = chip_shadow
        board[y0:y1, x1 : x1 + 2] = chip_shadow
        board[y0:y1, x0:x1] = chip_body
        board[y0 - 2 : y0, x0:x1:3] = chip_pin
        board[y1 : y1 + 2, x0:x1:3] = chip_pin
        board[y0:y1:3, x0 - 2 : x0] = chip_pin
        board[y0:y1:3, x1 : x1 + 2] = chip_pin


def _draw_pcb_vias(board: NDArray[np.uint8], *, seed: int) -> None:
    height, width = board.shape[:2]
    rng = np.random.default_rng(seed)
    via_outer = np.array([148, 156, 140], dtype=np.uint8)
    via_inner = np.array([96, 104, 92], dtype=np.uint8)
    for _ in range(48):
        cx = int(rng.integers(8, width - 8))
        cy = int(rng.integers(8, height - 8))
        board[cy - 2 : cy + 3, cx - 2 : cx + 3] = via_outer
        board[cy - 1 : cy + 2, cx - 1 : cx + 2] = via_inner


def _draw_pcb_connector(board: NDArray[np.uint8]) -> None:
    height, width = board.shape[:2]
    x0 = int(width * 0.04)
    y0 = int(height * 0.68)
    x1 = int(width * 0.16)
    y1 = int(height * 0.90)
    board[y0:y1, x0:x1] = (20, 30, 24)
    for row in range(y0 + 5, y1 - 5, 5):
        board[row : row + 3, x0 + 5 : x1 - 5 : 4] = (190, 196, 182)


def _draw_pcb_usb(board: NDArray[np.uint8]) -> None:
    height, width = board.shape[:2]
    x0 = int(width * 0.78)
    y0 = int(height * 0.72)
    x1 = int(width * 0.92)
    y1 = int(height * 0.88)
    board[y0:y1, x0:x1] = (24, 34, 28)
    board[y0 + 4 : y1 - 4, x0 + 6 : x1 - 6] = (180, 186, 174)


def _apply_board_shadow(board: NDArray[np.uint8]) -> None:
    height, width = board.shape[:2]
    shadow = board.astype(np.int16)
    shadow[:, 2:] = np.minimum(shadow[:, 2:] * 0.96, 255).astype(np.int16)
    shadow[2:, :] = np.minimum(shadow[2:, :] * 0.98, 255).astype(np.int16)
    board[:, :] = np.clip(shadow, 0, 255).astype(np.uint8)


def generate_snake_path_points(
    *,
    width: int = CANVAS_WIDTH,
    height: int = CANVAS_HEIGHT,
    cols: int = 16,
    rows: int = 12,
) -> list[tuple[float, float]]:
    """Generate a snake scan path covering the mock board area."""

    board_x, board_y, board_w, board_h = board_content_rect(width, height)
    margin_x = board_w * 0.08
    margin_y = board_h * 0.10
    inner_x = board_x + margin_x
    inner_y = board_y + margin_y
    inner_w = board_w - 2 * margin_x
    inner_h = board_h - 2 * margin_y
    step_x = inner_w / max(cols - 1, 1)
    step_y = inner_h / max(rows - 1, 1)

    points: list[tuple[float, float]] = []
    for row in range(rows):
        x_values = range(cols) if row % 2 == 0 else range(cols - 1, -1, -1)
        for col in x_values:
            points.append((inner_x + col * step_x, inner_y + row * step_y))
    return points


def create_mock_heatmap_qimage(
    width: int = CANVAS_WIDTH,
    height: int = CANVAS_HEIGHT,
    *,
    seed: int = 20260625,
) -> QImage:
    """Generate one smooth RGBA heatmap overlay aligned to the board."""

    field = _create_smooth_field(width, height, seed=seed)
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
    field[outside_board] *= 0.05

    rgb = _apply_spectral_lut(field)
    alpha = np.full((height, width), 150, dtype=np.uint8)
    alpha[outside_board] = 0
    rgba = np.dstack((rgb, alpha))
    return _array_to_qimage(rgba, rgba=True)


def _create_smooth_field(width: int, height: int, *, seed: int) -> NDArray[np.float64]:
    """Build a blurred multi-hotspot scalar field centered on the board."""

    y_coords, x_coords = np.mgrid[0:height, 0:width]
    field = np.zeros((height, width), dtype=np.float64)
    board_x, board_y, board_w, board_h = board_content_rect(width, height)

    hotspots = (
        (board_x + board_w * 0.52, board_y + board_h * 0.48, 95.0, 1.0),
        (board_x + board_w * 0.38, board_y + board_h * 0.35, 75.0, 0.65),
        (board_x + board_w * 0.62, board_y + board_h * 0.62, 85.0, 0.55),
        (board_x + board_w * 0.28, board_y + board_h * 0.58, 60.0, 0.40),
    )
    for cx, cy, sigma, weight in hotspots:
        field += weight * np.exp(-((x_coords - cx) ** 2 + (y_coords - cy) ** 2) / (2 * sigma**2))

    for _ in range(5):
        field = _box_blur(field, kernel=9)
    field -= field.min()
    maximum = field.max()
    if maximum > 0:
        field /= maximum
    return field


def _box_blur(values: NDArray[np.float64], *, kernel: int) -> NDArray[np.float64]:
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
    scaled = values * 4.0
    red = np.clip(1.5 - np.abs(scaled - 3.0), 0.0, 1.0)
    green = np.clip(1.5 - np.abs(scaled - 2.0), 0.0, 1.0)
    blue = np.clip(1.5 - np.abs(scaled - 1.0), 0.0, 1.0)
    return np.dstack(
        (
            (red * 255.0).astype(np.uint8),
            (green * 255.0).astype(np.uint8),
            (blue * 255.0).astype(np.uint8),
        )
    )


def _array_to_qimage(array: NDArray[np.uint8], *, rgba: bool = False) -> QImage:
    height, width = array.shape[:2]
    if rgba:
        image = QImage(array.data, width, height, width * 4, QImage.Format.Format_RGBA8888)
    else:
        image = QImage(array.data, width, height, width * 3, QImage.Format.Format_RGB888)
    return image.copy()
