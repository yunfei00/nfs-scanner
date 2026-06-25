# ADR-0002: Use QGraphicsView for Photo and Overlay Visualization

## Status

Accepted

## Context

The product must display camera photos, heatmaps, scan paths, markers, annotations and measurement overlays in one synchronized workspace.

Users need zoom, pan, alignment editing, marker interaction and export.

## Decision

Use `QGraphicsView` and `QGraphicsScene` as the main visualization architecture for the real-time and offline analysis views.

Each visual concept is represented as a scene item or layer.

## Alternatives Considered

### Plain QWidget Painting

Rejected because it makes interaction, selection, zooming and multiple layers harder to maintain.

### Matplotlib Embedded View

Rejected for the main interactive canvas because it is less suitable for rich object interaction and overlay editing.

### PyQtGraph ImageView Only

Useful for quick matrix display, but not enough for photo + alignment + marker + annotation workflow.

## Consequences

Benefits:

- Natural support for layered graphics.
- Zoom and pan can apply to all layers together.
- Markers and annotations can be interactive.
- Future alignment editor fits the same model.

Costs:

- More initial engineering than simple image widgets.
- Requires careful coordinate mapping.

## Rules

- Photo, heatmap, scan path and markers must share one scene coordinate system.
- Do not create separate independent views for photo and heatmap.
- Export should use the same scene state when possible.
