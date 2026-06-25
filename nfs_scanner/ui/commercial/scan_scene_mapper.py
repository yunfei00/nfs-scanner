"""Map scan-region coordinates to commercial canvas scene coordinates."""

from __future__ import annotations

from nfs_scanner.core.path_planner import ScanPoint3D
from nfs_scanner.core.scan_config import ScanRegion
from nfs_scanner.ui.commercial.graphics.mock_assets import CANVAS_HEIGHT, CANVAS_WIDTH, board_content_rect


def map_point_to_scene(
    x_mm: float,
    y_mm: float,
    region: ScanRegion,
    *,
    canvas_width: int = CANVAS_WIDTH,
    canvas_height: int = CANVAS_HEIGHT,
) -> tuple[float, float]:
    """Map one scan coordinate to scene pixel space aligned with the mock board."""

    board_x, board_y, board_w, board_h = board_content_rect(canvas_width, canvas_height)
    width_mm = region.x_stop - region.x_start
    height_mm = region.y_stop - region.y_start
    if abs(width_mm) < 1e-9:
        width_mm = 1.0
    if abs(height_mm) < 1e-9:
        height_mm = 1.0

    ratio_x = (x_mm - region.x_start) / width_mm
    ratio_y = (y_mm - region.y_start) / height_mm
    scene_x = board_x + ratio_x * board_w
    scene_y = board_y + ratio_y * board_h
    return scene_x, scene_y


def map_points_to_scene(
    points: list[ScanPoint3D],
    region: ScanRegion,
    *,
    canvas_width: int = CANVAS_WIDTH,
    canvas_height: int = CANVAS_HEIGHT,
) -> list[tuple[float, float]]:
    """Map preview points into scene coordinates for ScanPathLayer."""

    return [
        map_point_to_scene(x_mm, y_mm, region, canvas_width=canvas_width, canvas_height=canvas_height)
        for x_mm, y_mm, _z in points
    ]
