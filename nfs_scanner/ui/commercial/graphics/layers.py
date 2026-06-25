"""Scene layer placeholders."""

from __future__ import annotations

from enum import Enum


class LayerKind(str, Enum):
    """Stable layer identifiers."""

    PHOTO = "photo"
    HEATMAP = "heatmap"
    PATH = "path"
    MARKER = "marker"
    ANNOTATION = "annotation"


class PhotoLayer:
    """Photo layer placeholder. Expanded in Task 04."""


class HeatmapLayer:
    """Heatmap layer placeholder. Expanded in Task 05."""


class ScanPathLayer:
    """Scan path layer placeholder. Expanded in Task 06."""


class MarkerLayer:
    """Marker layer placeholder. Expanded in Task 07."""


class AnnotationLayer:
    """Annotation layer placeholder."""
