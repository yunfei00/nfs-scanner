"""Display density policy for ScanPathLayer rendering."""

from __future__ import annotations

from enum import Enum

FULL_DETAIL_LIMIT = 80
REDUCED_DETAIL_LIMIT = 250
HIGH_DENSITY_LIMIT = 400


class PathDisplayLevel(str, Enum):
    """How densely path markers are drawn for a given point count."""

    FULL = "full"
    REDUCED = "reduced"
    MINIMAL = "minimal"


def resolve_display_level(point_count: int) -> PathDisplayLevel:
    """Pick a display level from the number of preview points."""

    if point_count <= FULL_DETAIL_LIMIT:
        return PathDisplayLevel.FULL
    if point_count <= HIGH_DENSITY_LIMIT:
        return PathDisplayLevel.REDUCED
    return PathDisplayLevel.MINIMAL


def select_dot_indices(point_count: int, level: PathDisplayLevel) -> list[int]:
    """Return point indices to render as visible dots."""

    if point_count <= 0:
        return []
    if level == PathDisplayLevel.FULL:
        return list(range(point_count))
    if level == PathDisplayLevel.REDUCED:
        step = max(point_count // 40, 2)
        indices = list(range(0, point_count, step))
        if point_count - 1 not in indices:
            indices.append(point_count - 1)
        return sorted(set(indices))

    if point_count <= 4:
        return list(range(point_count))
    step = max(point_count // 6, 1)
    indices = [0, *range(step, point_count - 1, step), point_count - 1]
    return sorted(set(indices))


def select_arrow_segment_indices(point_count: int, level: PathDisplayLevel) -> list[int]:
    """Return path segment indices that should show direction arrows."""

    segment_count = max(point_count - 1, 0)
    if segment_count == 0:
        return []
    if level == PathDisplayLevel.FULL:
        return list(range(segment_count))
    if level == PathDisplayLevel.REDUCED:
        step = max(segment_count // 20, 3)
        indices = list(range(0, segment_count, step))
        if segment_count - 1 not in indices:
            indices.append(segment_count - 1)
        return indices

    step = max(segment_count // 4, 1)
    return list(range(0, segment_count, step))[-2:]


def path_line_width(level: PathDisplayLevel) -> float:
    """Stroke width for the main path polyline."""

    if level == PathDisplayLevel.FULL:
        return 2.0
    if level == PathDisplayLevel.REDUCED:
        return 1.6
    return 1.25


def is_high_density_preview(point_count: int) -> bool:
    """Return whether the preview should show a high-density warning."""

    return point_count > HIGH_DENSITY_LIMIT
