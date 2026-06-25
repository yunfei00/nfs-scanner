# 02 UI Architecture

## 1. Goal

The commercial UI must look like a professional instrument application while remaining maintainable and responsive.

It must support both laptop and desktop usage.

## 2. Main UI Components

```text
MainShell
  TopToolbar
  LeftArea
    WorkflowPanel
    DeviceStatusPanel
  WorkspaceTabs
    RealtimeView
    DataView
    ThreeDView
    DataTableView
    ReportView
    DeviceCenterView
  PropertyPanel
    ScanParametersTab
    DisplaySettingsTab
    InstrumentSettingsTab
  BottomDock
    SpectrumPanel
    StatisticsPanel
    LogPanel
  StatusBar
```

## 3. Component Responsibilities

### MainShell

Owns the top-level layout.

Responsibilities:

- create splitters and dock regions
- load theme
- restore layout state
- route high-level navigation

Not responsible for:

- scan execution
- device communication
- heatmap calculation

### WorkspaceTabs

Hosts the main work modes.

Required modes:

- Real-time View
- Data View
- 3D View
- Data Table

Future modes:

- Report Center
- Device Center

### RealtimeView

Owns the live scanning visual workspace.

Contains:

- graphics canvas
- local view toolbar
- optional mini-map or colorbar

### PropertyPanel

Shows editable parameters.

Rules:

- must be scrollable
- must use cards or collapsible sections
- must not contain raw logs
- must avoid taking excessive width from the canvas

### BottomDock

Shows data that supports the current task:

- spectrum
- scan statistics
- logs

On small screens it switches to tab mode.

## 4. Communication Pattern

UI should use signals or service method calls:

```text
Button click
  -> View emits intent
  -> Service handles command
  -> Service emits state update
  -> View updates display
```

Avoid this:

```text
Button click
  -> Widget directly talks to serial port
```

## 5. State Ownership

| State | Owner |
|---|---|
| current project | ProjectService |
| current scan job | ScanRuntimeService / ScanManager |
| current device connection status | DeviceService |
| current visualization options | ViewModel or UI settings object |
| theme | ThemeManager |
| persistent layout | QSettings / ConfigManager |

## 6. Responsiveness Rules

At width below 1500px:

- left workflow collapses
- toolbar hides secondary text
- bottom dock uses tabs

At height below 800px:

- bottom dock is minimized
- logs are hidden behind tab
- central canvas keeps priority

## 7. UI Testing Targets

For each UI task, verify:

- app starts
- no layout overlap at 1366x768
- no unreadable text on dark theme
- no critical button hidden without access
- central canvas remains visible
