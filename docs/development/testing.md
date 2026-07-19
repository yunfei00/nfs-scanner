# Testing Guide

## 1. Testing Goals

Testing should protect:

- app startup
- scan path planning
- device adapter behavior
- data parsing compatibility
- heatmap generation
- UI construction

## 2. Test Levels

### Unit Tests

Use for:

- path planning
- frequency data parsing
- heatmap matrix generation
- configuration parsing
- state machines

### Integration Tests

Use for:

- mock scan workflow
- mock device connections
- project load/save
- offline analysis load

### UI Smoke Tests

Use for:

- main window construction
- unified scan-control page construction
- scrollable workspace and user-facing table headers
- stable handler imports after structural refactoring

## 3. Mock Devices

Mock devices are required for development without hardware.

Mock devices should simulate:

- successful connection
- timeout
- invalid response
- slow acquisition
- stop during scan

## 4. Manual Verification

For UI tasks, include manual notes:

- tested resolution
- app start command
- screenshot if possible
- known limitations

The headless structural check is `python tools/unified_ui_check.py`.

## 5. Minimum Check for AI Tasks

If no full test suite is available, run at least:

- import check
- app startup check if environment supports GUI
- targeted unit tests for changed logic

## 6. Regression Areas

Always watch:

- existing CSV formats
- scan start/stop behavior
- device connection behavior
- heatmap display alignment
- UI responsiveness
