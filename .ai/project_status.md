# Project Status

Last updated: 2026-06-25

## Current Mode

**STOP — Sprint 014 Major Review Gate**

Sprints 011–013 complete. **Real device control not approved.**

## Sprint Progress

| Sprint | Status | Notes |
|--------|--------|-------|
| Sprint 001–010 | done | Shell through integration prep |
| Sprint 011 | done | Device Center UX (mock) |
| Sprint 012 | done | Device configuration models |
| Sprint 013 | done | Dry-run command layer |
| Sprint 014 | **Major Review Gate** | Before real hardware control |
| Real Device Control | **blocked** | Separate Major Review required |

## Next Actions (Human)

1. Review `.ai/daily/2026-06-25-sprint014-major-review-gate.md`
2. Verify Device Center + mock scan dry-run logs in commercial UI
3. Approve or redirect before any real hardware control Sprint

## Application Entry Points

- Legacy UI (default): `python -m nfs_scanner.main`
- Commercial UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`

## Recent Capabilities (Sprint 011–013)

- Device Center: connect/disconnect/refresh + config editing (in-memory)
- Sidebar device summary syncs with Device Center
- Dry-run motion/spectrum/camera command log during mock scan
- `DRY RUN - NO HARDWARE CONTROL` labeling in logs

## Constraints (unchanged)

- No real device commands, ScanManager, or CSV changes until approved.
- `REAL_DEVICE_ENABLED=false`; do not set `NFS_SCANNER_REAL_DEVICES=1` without approval.
