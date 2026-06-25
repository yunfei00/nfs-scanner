# V1.0 Milestones

This file defines V1.0 milestones and their success criteria.

## M1 Commercial UI Shell

Corresponding phase: Phase 1.

Success criteria:

- The new commercial UI Shell can be opened.
- The old UI remains available.
- The shell contains the expected major regions: toolbar, workflow, device status, workspace, property panel, bottom dock, and status bar.

## M2 Realtime Workspace

Corresponding phase: Phase 2.

Success criteria:

- The central `QGraphicsView` canvas can display mock photo, mock heatmap, mock path, and mock marker.
- Photo, heatmap, path, and marker layers stay aligned during zoom and pan.
- Heatmap is rendered as a single image layer.

## M3 Scan Config + Preview

Corresponding phase: Phase 3.

Success criteria:

- Changing scan parameters previews the scan path.
- Point count and estimated time are recalculated.
- The UI can show area and template information without connecting real hardware.

## M4 Device Center

Corresponding phase: Phase 4.

Success criteria:

- Device connection configuration is moved out of the main shell.
- The main shell only shows device status summaries.
- Device diagnostics live in Device Center.

## M5 Runtime Integration

Corresponding phase: Phase 5.

Success criteria:

- The new UI can execute one complete mock or real scan workflow.
- Runtime integration preserves existing scan behavior and data compatibility.

## M6 Data Analysis

Corresponding phases: Phase 6, Phase 7, Phase 8.

Success criteria:

- Historical data can be analyzed offline.
- Data table and 3D views are usable.
- Canvas linkage works for analysis workflows.

## M7 Report + Release

Corresponding phases: Phase 9, Phase 10.

Success criteria:

- A demo build can be packaged.
- Reports can be generated.
- Demo projects, user manual, and presentation workflow are available.
