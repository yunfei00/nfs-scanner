# 05 Implementation Roadmap

## Phase 1 - UI Shell

Build the commercial main window layout:

- top toolbar
- left workflow
- device status cards
- central workspace tabs
- right property panel
- bottom dock
- status bar
- dark professional theme
- responsive layout

Acceptance:

- 1366x768 is usable.
- 1920x1080 is comfortable.
- central canvas keeps the highest priority.

## Phase 2 - Real-time Canvas

Build the core QGraphicsView canvas:

- photo layer
- heatmap layer
- scan path layer
- marker layer
- colorbar
- opacity
- zoom and pan

Acceptance:

- all layers zoom together.
- heatmap is a single image layer.

## Phase 3 - Scan Parameters

Implement parameter panel and path preview:

- start and end coordinates
- step values
- point count
- area
- path length
- estimated time
- snake path preview

Acceptance:

- parameter changes update preview and statistics.

## Phase 4 - Device Center

Implement a separate device center:

- motion platform
- spectrum instrument
- camera
- connection test
- device logs
- plugin list

Acceptance:

- main UI only shows device summaries.

## Phase 5 - Runtime Integration

Connect existing scan logic to the new UI:

- run scan
- pause and resume
- update current point
- save point data
- update heatmap
- update statistics

Acceptance:

- the new UI can complete one scan workflow.

## Phase 6 - Data View

Implement offline analysis:

- task list
- trace selection
- frequency selection
- display mode
- LUT
- offline heatmap
- export image and CSV

Acceptance:

- historical scan data can be reloaded and analyzed.

## Phase 7 - Data Table

Implement table view:

- sort
- filter
- search
- export
- selected row links to canvas and spectrum

Acceptance:

- selected data point can be located visually.

## Phase 8 - 3D View

Implement 3D heatmap surface:

- rotate
- pan
- zoom
- surface mode
- wireframe mode

Acceptance:

- current heatmap can be displayed in 3D.

## Phase 9 - Report Center

Implement report generation:

- project info
- device info
- scan parameters
- heatmap image
- spectrum image
- marker table
- PDF output

Acceptance:

- one report can be generated from current project.
