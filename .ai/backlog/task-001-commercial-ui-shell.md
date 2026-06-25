# Task 001 - Commercial UI Shell

## Goal

Create the first commercial UI shell for NFS Scanner while keeping the existing working UI and scan logic available.

## Required Reading

- `docs/product-spec/01_design_system.md`
- `docs/product-spec/02_main_window_layout.md`
- `docs/product-spec/03_work_modes.md`
- `docs/product-spec/06_codex_tasks.md`

## Scope

Implement a new shell module instead of rewriting the current UI in place.

Required regions:

- top toolbar
- left workflow panel
- device status cards
- central workspace tabs
- right property panel
- bottom dock
- status bar

## Suggested Files

The exact structure may be adjusted after inspecting the current codebase.

Recommended additions:

- `nfs_scanner/ui/commercial/`
- `nfs_scanner/ui/commercial/main_shell.py`
- `nfs_scanner/ui/commercial/workflow_panel.py`
- `nfs_scanner/ui/commercial/device_status_panel.py`
- `nfs_scanner/ui/commercial/property_panel.py`
- `nfs_scanner/ui/commercial/bottom_dock.py`
- `nfs_scanner/ui/commercial/workspace.py`

## Constraints

- Do not delete the existing `ScanControlPage`.
- Do not break current app startup.
- Do not connect real devices yet unless already trivial.
- Placeholder content is acceptable for this task.
- Use layouts and splitters, not fixed absolute positioning.

## Acceptance Criteria

- The app starts successfully.
- The new shell can be launched or toggled from the app entry point.
- Layout is usable at 1366x768.
- Layout is comfortable at 1920x1080.
- Left workflow can be collapsed or designed for future collapse.
- Right panel is scrollable.
- Bottom area can be represented as tabs on small screens.
- No existing scan workflow is removed.

## Completion Note

When complete, summarize:

- files changed
- how to run
- screenshots if available
- any limitations
