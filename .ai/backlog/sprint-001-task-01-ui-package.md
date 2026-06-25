# Sprint 001 Task 01 - Commercial UI Package

## Goal

Create the commercial UI package and a safe entry point.

## Read First

- `.ai/codex.md`
- `docs/sprints/sprint-001-commercial-ui-shell.md`
- `docs/architecture/01_directory_structure.md`
- `docs/adr/ADR-0001-commercial-ui-shell.md`

## Scope

- Add `nfs_scanner/ui/commercial/`.
- Add placeholder modules for main shell, toolbar, workflow, device status, workspace, property panel, bottom dock and status bar.
- Keep old UI available.

## Acceptance

- App imports successfully.
- Existing startup is not broken.
- New package can be imported.
- No device or scan logic is changed.
