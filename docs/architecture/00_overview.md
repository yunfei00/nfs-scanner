# 00 Architecture Overview

## 1. Purpose

This document defines the target architecture for NFS Scanner.

The architecture must support three stages:

1. Current PySide6 engineering version.
2. Commercial PySide6 product version.
3. Future high-performance Qt/C++ version.

The architecture should keep product decisions, UI layout, scan logic, device adapters, data storage and report generation separated.

## 2. Target Layers

```text
UI Layer
  Commercial Shell
  Work Modes
  Visualization Widgets
  Dialogs

Application Layer
  ProjectService
  ScanRuntimeService
  AnalysisService
  ReportService
  DeviceService

Core Layer
  ScanManager
  PathPlanner
  AlignmentManager
  HeatmapManager
  FrequencyData
  Models

Device Layer
  Motion Adapter
  Spectrum Adapter
  Camera Adapter
  Plugin Loader

Infrastructure Layer
  Storage
  Config
  Logging
  License
  Theme
```

## 3. Layer Rules

### UI Layer

Allowed:

- show widgets
- collect user input
- emit commands to services
- render visual data passed from services or managers

Not allowed:

- direct serial communication
- direct VISA calls
- direct hardware SDK calls
- writing raw scan data formats without storage service

### Application Layer

Allowed:

- coordinate UI commands and core managers
- manage workflows
- convert UI requests into scan jobs
- expose clean signals for UI updates

Not allowed:

- painting widgets
- storing UI-only state
- vendor-specific device commands

### Core Layer

Allowed:

- path planning
- scan state models
- alignment transforms
- heatmap matrix generation
- frequency data parsing

Not allowed:

- creating Qt widgets
- talking directly to hardware
- reading user interface controls

### Device Layer

Allowed:

- connect to hardware
- expose adapter APIs
- hide vendor-specific protocols
- report device status and errors

Not allowed:

- controlling UI layout
- deciding scan workflow
- writing report files

### Infrastructure Layer

Allowed:

- file storage
- configuration persistence
- logging
- local license checks
- theme loading

Not allowed:

- scan orchestration
- business decisions
- UI workflow decisions

## 4. Main Data Flow

```text
User Action
  -> UI Command
  -> Application Service
  -> Core Manager
  -> Device Adapter
  -> Measurement Result
  -> Storage
  -> Analysis/Heatmap
  -> UI Signal
  -> Visualization Update
```

## 5. Runtime Goals

- UI must remain responsive during scans.
- Device failures must be converted to clear user-visible errors.
- Partial scan data must remain usable after stop or failure.
- Real-time view and offline data view should reuse heatmap and frequency data logic.

## 6. Migration Strategy

Do not replace the current UI in one step.

Recommended migration:

1. Add commercial UI shell beside existing UI.
2. Add mock visualization and placeholder panels.
3. Connect existing scan managers to the new UI.
4. Move advanced device setup into Device Center.
5. Move offline analysis into Data View.
6. Retire old UI only after parity is reached.
