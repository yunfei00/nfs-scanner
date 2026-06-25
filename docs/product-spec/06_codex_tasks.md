# 06 Codex Tasks

This file is the execution queue for coding agents.

## Task 001 - Create Commercial UI Shell

Goal:

Create the new commercial main window shell without removing existing working logic.

Scope:

- Add a new UI shell module.
- Keep existing UI available during migration.
- Add top toolbar, workflow panel, workspace area, property panel, bottom dock and status bar.
- Add placeholder widgets for all major regions.

Acceptance:

- App starts successfully.
- New shell can be opened.
- Layout works at 1366x768 and 1920x1080.
- No existing scan logic is broken.

## Task 002 - Add Theme System

Goal:

Create a central theme and QSS system.

Scope:

- Add theme file for dark professional theme.
- Define colors through object names and component classes.
- Remove scattered hard-coded UI colors when touching related files.

Acceptance:

- Main UI uses consistent colors.
- Buttons, cards, inputs and tabs share the same visual language.

## Task 003 - Workflow Panel

Goal:

Implement left workflow steps.

Steps:

1. Project Management
2. Device Connection
3. Area Alignment
4. Scan Configuration
5. Scan Execution
6. Data Analysis
7. Report Export

Acceptance:

- Current step is highlighted.
- Completed steps show success state.
- Panel can collapse to icon-only mode.

## Task 004 - Device Status Cards

Goal:

Implement device status cards in the left panel.

Cards:

- Motion Platform
- Spectrum Instrument
- Camera

Acceptance:

- Each card shows name, model, address and connection state.
- States use consistent badges.
- A button opens Device Center.

## Task 005 - Real-time Canvas

Goal:

Implement QGraphicsView-based canvas.

Layers:

- photo layer
- heatmap layer
- scan path layer
- marker layer
- annotation layer

Acceptance:

- Zoom and pan work.
- Layers stay aligned.
- Empty state is visually clean.

## Task 006 - Heatmap Image Layer

Goal:

Render heatmap as a single image overlay.

Acceptance:

- No per-cell drawing.
- Opacity works.
- LUT switch works.
- Colorbar updates.

## Task 007 - Scan Path Preview

Goal:

Generate visual preview from scan parameters.

Acceptance:

- Snake path preview is visible.
- Point count and estimated time update.
- Invalid ranges show clear UI warnings.

## Task 008 - Property Panel

Goal:

Implement right-side property panel tabs.

Tabs:

- Scan Parameters
- Display Settings
- Instrument Settings

Acceptance:

- Panel is scrollable.
- Inputs use consistent style.
- Start scan button is clearly visible.

## Task 009 - Bottom Dock

Goal:

Implement bottom dock panels.

Panels:

- Spectrum
- Scan Statistics
- Logs

Acceptance:

- On large screens panels can be shown together.
- On small screens they switch to tab mode.

## Task 010 - Data View

Goal:

Implement offline analysis page.

Acceptance:

- Historical scan task can be loaded.
- Trace and frequency can be selected.
- Heatmap refreshes without connected devices.

## Task 011 - Data Table

Goal:

Implement scan point data table.

Acceptance:

- Sort, filter, search and export are available.
- Selecting a row links to visual location.

## Task 012 - 3D View

Goal:

Implement first 3D heatmap surface view.

Acceptance:

- Current heatmap matrix can be displayed as a surface.
- Rotation and zoom work.

## Task 013 - Report Center

Goal:

Implement first report export workflow.

Acceptance:

- Project information, device information, scan parameters, heatmap and spectrum can be exported to a PDF report.

## Task 014 - Device Center

Goal:

Move advanced device setup out of the main scan screen.

Acceptance:

- Motion, Spectrum and Camera have separate setup sections.
- Device test results are visible.
- Main screen stays focused on scanning.
