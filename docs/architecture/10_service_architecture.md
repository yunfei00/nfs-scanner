# Service Architecture

This document defines the future service layer for the commercial NFS Scanner architecture.

The service layer separates UI widgets from core workflow, device adapters, storage, and analysis logic. It is a planning document for future implementation and does not require current code changes.

## Planned Services

- `ProjectService`
- `DeviceService`
- `ScanRuntimeService`
- `AnalysisService`
- `ReportService`
- `ThemeService` / `ThemeManager`
- `ConfigService`

## Responsibilities

### ProjectService

Manages project creation, opening, saving, and historical scan tasks.

It owns project-level workflow state but does not create UI widgets.

### DeviceService

Manages device status, connection, disconnection, and device summaries.

It does not directly control UI. It exposes device status and operations to UI through service methods and signals/events.

### ScanRuntimeService

Manages scan task state, start, pause, stop, and resume.

It owns scan runtime orchestration and should keep long-running operations off the UI thread.

### AnalysisService

Handles offline data loading, Trace/Frequency switching, and heatmap data preparation.

It prepares data for visualization but does not render UI widgets.

### ReportService

Collects report data and exports reports.

It should depend on stable data/export APIs rather than scraping UI state.

### ThemeManager

Loads QSS and manages theme switching.

It provides one central place for theme application and avoids hard-coded styles in UI code.

### ConfigService

Saves and restores configuration, user preferences, layout state, and profiles.

It should keep configuration persistence independent from individual widgets.

## Rules

- UI calls business behavior through services.
- Services call core, device, and storage layers.
- Device code must not call UI.
- All long-running operations must consider worker/thread execution.
- Service APIs should be small and task-oriented.
- Services should be testable without launching the full UI.
