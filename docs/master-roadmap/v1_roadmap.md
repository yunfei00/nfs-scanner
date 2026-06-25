# V1.0 Roadmap

This file defines the high-level V1.0 roadmap. It is intentionally not a large task breakdown. Current execution should only expand Phase 1 and Phase 2. Phase 3 and later remain summaries until earlier phases are complete.

## Phase 0 - Product Spec / Architecture / AI Workflow

Status: done.

Goal: establish the product specification, architecture documents, ADRs, design system, UI specs, AI workflow rules, assumptions, review gates, and backlog structure.

## Phase 1 - Commercial UI Shell

Status: in progress / Sprint 001 done.

Goal: complete the commercial UI shell, including toolbar, workflow panel, device status area, workspace tabs, property panel, bottom dock, status bar, theme foundation, and safe entry path while preserving the old UI.

## Phase 2 - Realtime Workspace

Status: next active phase.

Goal: complete the first central realtime canvas for the commercial UI.

Scope:

- `QGraphicsView` / `QGraphicsScene`
- `PhotoLayer`
- `HeatmapLayer`
- `ScanPathLayer`
- `MarkerLayer`
- `ColorBar`
- `MiniMap`
- Zoom, pan, fit, and reset interactions

Phase 2 uses mock data and placeholders only. It must not connect real scan runtime or real devices.

## Phase 3 - Scan Configuration

Status: summary only.

Goal: complete right-side scan parameters, path preview, point count, area calculation, estimated time, and parameter templates.

Do not expand this phase until Phase 1 and Phase 2 are stable.

## Phase 4 - Device Center

Status: summary only.

Goal: move motion platform, spectrum instrument, and camera connection/diagnostics into Device Center. The main shell should only show device status summaries.

## Phase 5 - Scan Runtime Integration

Status: summary only.

Goal: gradually connect existing scan logic into the new commercial UI after the shell, realtime canvas, scan configuration, and device center are stable.

## Phase 6 - Data View

Status: summary only.

Goal: load historical scan tasks offline, switch Trace/Frequency views, and regenerate heatmaps.

## Phase 7 - Data Table

Status: summary only.

Goal: provide scan point tables, search, filtering, export, and canvas linkage.

## Phase 8 - 3D View

Status: summary only.

Goal: display 3D Surface, Mesh, and Wireframe views.

## Phase 9 - Report Center

Status: summary only.

Goal: generate PDF reports with one workflow.

## Phase 10 - Release Preparation

Status: summary only.

Goal: prepare packaging, demo projects, user manual, and demonstration workflows.

## Execution Rule

Cursor/Codex should focus on Phase 1 and Phase 2 only. Phase 3 and later should not be expanded into detailed tasks until the preceding phases are complete and reviewed.
