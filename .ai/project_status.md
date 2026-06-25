# Project Status

Last updated: 2026-06-25

## Current Mode

**Autopilot allowed** — Soft Review Gate between Sprints; stop only at Major Review Gate or Stop Conditions.

## Sprint Progress

| Sprint | Status | Notes |
|--------|--------|-------|
| Sprint 001 | done | Commercial UI Shell |
| Sprint 002 | done | Realtime Workspace |
| Sprint 003 | done | Commercial Widget Library |
| Sprint 004 | done | Commercial Layout Polish |
| Sprint 005 | done | Scan Configuration + Path Preview |
| Sprint 006 | done | Scan Preview UX Polish |
| Sprint 007 | done | Mock Scan Runtime |
| Sprint 008 | **next** | Mock Scan Progress + Logs |
| Sprint 009 | planned | Data View Mock |
| Sprint 010 | blocked until Major Review | Before Real Device Integration |

## Next Actions (Autopilot)

1. Start **Sprint 008 — Mock Scan Progress, Logs and Runtime Controls**.
2. Continue through Sprint 009 without pausing for human review.
3. **Stop before Sprint 010** — Major Review Gate (real device / real scan integration).

## Major Review Gate

Next mandatory stop: **before Sprint 010 / real device integration / real scan runtime / CSV format changes**.

## Application Entry Points

- Legacy UI (default): `python -m nfs_scanner.main`
- Commercial UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`

## Recent Capabilities (Sprint 007)

- `MockScanRuntimeService` drives point-by-point mock scan without ScanManager.
- Property panel and toolbar start/stop buttons wired via `MockScanController`.
- `ScanPathLayer` shows completed segment, current marker, and dot coloring during mock scan.

## Recent Capabilities (Sprint 005–006)

- PropertyPanel scan params drive ScanPathLayer preview (snake/raster).
- Preview stats in property panel and bottom dock.
- High-density path display policy (>400 points sampled).
- NFSNumericField with units; selective fit / auto-fit checkbox.

## Constraints (unchanged)

- No real device, real scan execution, or CSV format changes until Major Review.
- Old UI must remain available.
