# Project Status

Last updated: 2026-06-25

## Current Mode

**STOP — Sprint 016 Major Review Gate**

Sprint 015 complete (motion connection test only). **Real motion control not approved.**

## Sprint Progress

| Sprint | Status | Notes |
|--------|--------|-------|
| Sprint 001–014 | done | Through dry-run layer + review |
| Sprint 015 | done | Motion connection test only (no motion commands) |
| Sprint 016 | **Major Review Gate** | Before real motion control |
| Real Motion Control | **blocked** | Separate Major Review required |

## Next Actions (Human)

1. Review `.ai/daily/2026-06-25-sprint016-major-review-gate.md`
2. Optionally test real serial connect with `NFS_SCANNER_REAL_DEVICES=1`
3. Approve before any jog/home/move Sprint

## Application Entry Points

- Legacy UI: `python -m nfs_scanner.main`
- Commercial UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`

## Recent Capabilities (Sprint 015)

- Motion config: mock vs `real_connection_test`
- Serial port discovery (optional pyserial)
- Device Center real connect/disconnect with read-only connection log
- `MotionConnectionAdapter` — open/close serial only

## Constraints

- No motion commands (home/jog/move/G-code).
- No spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
