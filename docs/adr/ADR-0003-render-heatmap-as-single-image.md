# ADR-0003: Render Heatmap as a Single Image Layer

## Status

Accepted

## Context

Near-field scan heatmaps are often zoomed and overlaid on camera images.

If the heatmap is drawn cell by cell, zooming can show grid gaps, aliasing or inconsistent alignment.

## Decision

Render each heatmap as one RGBA image layer.

The heatmap matrix is converted to RGBA using the selected LUT and range settings, then converted to QImage/QPixmap and placed into the scene as one item.

## Alternatives Considered

### Cell-by-cell QPainter Rectangles

Rejected because it can create visible gaps and is harder to keep smooth at high zoom levels.

### Table Widget Color Cells

Rejected because it is not a scientific visualization canvas.

### Matplotlib Figure Export Only

Useful for reports, but not suitable as the live interactive layer.

## Consequences

Benefits:

- No visible cell gaps.
- Smooth overlay on camera photos.
- Opacity is simple.
- Export matches visual state.

Costs:

- Need LUT manager and image generation pipeline.
- Need efficient updates for large matrices.

## Rules

- Do not draw heatmap cells one by one in the main visualization.
- Use a single image item for the active heatmap layer.
- LUT, vmin/vmax and opacity must update the image layer consistently.
