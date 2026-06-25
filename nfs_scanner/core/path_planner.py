"""Pure scan path preview planner for commercial UI."""

from __future__ import annotations

import math

from .scan_config import ScanPathConfig, ScanPreviewStats, ScanRegion

ScanPoint3D = tuple[float, float, float]


def generate_raster_points(region: ScanRegion, config: ScanPathConfig) -> list[ScanPoint3D]:
    """Generate row-major raster points inside the scan region."""

    _ = config
    safe_region = region.clamped()
    x_values = _axis_values(safe_region.x_start, safe_region.x_stop, safe_region.x_step)
    y_values = _axis_values(safe_region.y_start, safe_region.y_stop, safe_region.y_step)

    points: list[ScanPoint3D] = []
    for y_value in y_values:
        for x_value in x_values:
            points.append((x_value, y_value, safe_region.z_height))
    return points


def generate_snake_points(region: ScanRegion, config: ScanPathConfig) -> list[ScanPoint3D]:
    """Generate alternating-direction snake points inside the scan region."""

    _ = config
    safe_region = region.clamped()
    x_values = _axis_values(safe_region.x_start, safe_region.x_stop, safe_region.x_step)
    y_values = _axis_values(safe_region.y_start, safe_region.y_stop, safe_region.y_step)

    points: list[ScanPoint3D] = []
    for row_index, y_value in enumerate(y_values):
        row_x_values = x_values if row_index % 2 == 0 else list(reversed(x_values))
        for x_value in row_x_values:
            points.append((x_value, y_value, safe_region.z_height))
    return points


def generate_preview_points(region: ScanRegion, config: ScanPathConfig) -> list[ScanPoint3D]:
    """Generate preview points according to the configured scan mode."""

    safe_config = config.clamped()
    if safe_config.scan_mode == "raster":
        return generate_raster_points(region, safe_config)
    return generate_snake_points(region, safe_config)


def calculate_preview_stats(
    points: list[ScanPoint3D],
    region: ScanRegion,
    config: ScanPathConfig,
) -> ScanPreviewStats:
    """Calculate preview metrics from generated points."""

    safe_region = region.clamped()
    safe_config = config.clamped()
    point_count = len(points)
    width = abs(safe_region.x_stop - safe_region.x_start)
    height = abs(safe_region.y_stop - safe_region.y_start)
    area_mm2 = width * height
    path_length_mm = _path_length(points)
    travel_seconds = path_length_mm / max(safe_config.speed_mm_min / 60.0, 1e-6)
    dwell_seconds = point_count * safe_config.dwell_ms / 1000.0
    return ScanPreviewStats(
        point_count=point_count,
        area_mm2=area_mm2,
        path_length_mm=path_length_mm,
        estimated_seconds=travel_seconds + dwell_seconds,
        scan_mode=safe_config.scan_mode,
    )


def _axis_values(start: float, stop: float, step: float) -> list[float]:
    if step <= 0:
        return [start]

    values: list[float] = []
    value = start
    epsilon = max(abs(step) * 1e-6, 1e-9)
    while value <= stop + epsilon:
        values.append(round(value, 6))
        value += step
    if values and values[-1] > stop + epsilon:
        values.pop()
    if not values:
        values = [start]
    return values


def _path_length(points: list[ScanPoint3D]) -> float:
    if len(points) < 2:
        return 0.0

    total = 0.0
    for index in range(1, len(points)):
        x0, y0, _ = points[index - 1]
        x1, y1, _ = points[index]
        total += math.hypot(x1 - x0, y1 - y0)
    return total
