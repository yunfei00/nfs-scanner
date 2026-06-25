# Sprint 002 - Realtime Workspace

## Goal

Implement the first version of the commercial UI realtime central canvas.

## Scope

- `QGraphicsView` / `QGraphicsScene`
- `LayerManager`
- `PhotoLayer`
- `HeatmapLayer`
- `ScanPathLayer`
- `MarkerLayer`
- `ColorBar`
- `MiniMap`
- Zoom / Pan / Fit / Reset
- Use mock data only. Do not connect real scan logic.

## Explicitly Out of Scope

- Do not connect real devices.
- Do not connect real scan runtime.
- Do not change CSV or persisted data formats.
- Do not delete the old UI.
- Do not implement a complete 3D view.

## Acceptance

- The new commercial UI Realtime View shows a central canvas.
- The canvas can display a mock photo or placeholder board.
- The canvas can display one mock heatmap overlay as a single image layer.
- The canvas can display a mock snake scan path.
- The canvas can display a mock marker and tooltip.
- Layers stay aligned during zoom and pan.
- `python -m compileall nfs_scanner` passes.
- The old UI is not affected.
