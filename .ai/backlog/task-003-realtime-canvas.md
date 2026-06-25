# Task 003 - Real-time Canvas

## Goal

Implement the first version of the real-time visualization canvas.

## Required Reading

- `docs/product-spec/03_work_modes.md`
- `docs/product-spec/04_feature_specs.md`

## Scope

Build a QGraphicsView/QGraphicsScene based widget with these layers:

1. Photo layer
2. Heatmap layer
3. Scan path layer
4. Marker layer
5. Annotation layer

## Required Features

- Empty state display
- Load or set a photo pixmap
- Set heatmap as a single image overlay
- Set overlay opacity
- Show scan path preview
- Show marker items
- Zoom and pan
- Reset view

## Rules

- Heatmap must be one image layer, not cell-by-cell painting.
- Photo, heatmap, scan path and markers must share one coordinate system.
- This task may use mock data.
- Do not connect full scan runtime yet.

## Acceptance Criteria

- A demo photo/placeholder can be displayed.
- A demo heatmap overlay can be displayed.
- Opacity works.
- Zoom and pan keep all layers aligned.
- Marker and path stay aligned with the image.
