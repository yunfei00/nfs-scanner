# Project Status

Last updated: 2026-06-25

## Sprint

Sprint 004 - Commercial Layout Polish (completed, awaiting human review)

## Completed Tasks

### Sprint 001
- [x] Task 01-06 Commercial UI Shell

### Sprint 002
- [x] Task 01-10 Realtime Workspace
- [x] Review Fix - layer z-order

### Sprint 003
- [x] Task 01-04 Commercial Widget Library
- [x] Smoke test fix (QFormLayout)

### Sprint 004
- [x] Task 01 - RealtimeCanvas visual scale polish
- [x] Task 02 - Main shell splitter ratio polish
- [x] Task 03 - ColorBar / MiniMap polish
- [x] Task 04 - Left panel and bottom dock polish
- [x] Task 05 - Sprint review

## Review Gate

Sprint 004 stopped at review gate. Do not enter Sprint 005 until human review approves.

## Notes

- Legacy UI remains default: `python -m nfs_scanner.main`
- Commercial UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`
- Mock board now fills ~76% of scene; fit_view targets ~72% viewport fill.
- Left panel scrolls; bottom dock capped at 240px default max.
- No real device, scan runtime, or CSV format changes.

## Next Recommended

- Human review of central canvas visual prominence at 1366x768 and 1920x1080
- Sprint 005 planning after review approval
