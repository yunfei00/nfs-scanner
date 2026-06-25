# 06 Signal Flow

## 1. Goal

This document defines how commands and updates move through the application.

The goal is to keep UI responsive and avoid direct coupling between widgets and hardware.

## 2. Command Flow

```text
User clicks button
  -> UI emits intent
  -> Application service validates request
  -> Core manager creates or updates model
  -> Device service performs hardware action if needed
  -> Result is emitted back as state update
  -> UI updates display
```

## 3. Scan Start Flow

```text
Start Scan button
  -> RealtimeView / PropertyPanel emits start_scan_requested
  -> ScanRuntimeService validates project, devices and scan config
  -> PathPlanner generates scan points
  -> ScanManager creates scan job
  -> Worker thread starts scan loop
  -> UI receives scan_started signal
```

## 4. Point Acquisition Flow

```text
Worker moves platform
  -> motion adapter confirms position
  -> spectrum adapter acquires trace
  -> storage appends point and trace data
  -> HeatmapManager updates matrix
  -> UI receives point_acquired
  -> canvas updates heatmap/path/marker
  -> spectrum panel updates trace
  -> statistics panel updates progress
```

## 5. Device Status Flow

```text
Device connect request
  -> DeviceService
  -> Adapter connect
  -> status model update
  -> DeviceStatusPanel refresh
  -> DeviceCenter log entry
```

## 6. Error Flow

```text
Adapter error
  -> typed exception or error result
  -> DeviceService/ScanRuntimeService catches it
  -> state changes to error
  -> UI shows status badge and message
  -> log panel records details
```

## 7. UI Update Rule

Only the main UI thread may update Qt widgets.

Workers must communicate with signals, queues or service callbacks that return to the UI thread.

## 8. Event Categories

Recommended event categories:

- project_loaded
- device_status_changed
- scan_started
- scan_paused
- scan_resumed
- scan_stopped
- scan_completed
- point_started
- point_acquired
- heatmap_updated
- spectrum_updated
- error_reported
- log_appended

## 9. AI Agent Rule

If implementing a new feature, describe its event flow before writing complex code.
