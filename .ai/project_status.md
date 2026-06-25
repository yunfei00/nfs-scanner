# Project Status

Last updated: 2026-06-25

## Sprint

Sprint 003 - Commercial Widget Library (completed, awaiting human review)

## Completed Tasks

### Sprint 001
- [x] Task 01-06 Commercial UI Shell

### Sprint 002
- [x] Task 01-10 Realtime Workspace
- [x] Review Fix - layer z-order

### Sprint 003
- [x] Task 01 - NFS widget library (NFSCard, NFSPanel, NFSStatusBadge, buttons, NFSParameterGroup, NFSCollapsiblePanel, NFSDockPanel)
- [x] Task 02 - dark_professional.qss unified NFS styling
- [x] Task 03 - Migrate toolbar, workflow, device status, property, bottom dock, realtime toolbar
- [x] Task 04 - instrument_devices runtime cache gitignore + review gate

## Review Gate

Sprint 003 stopped at review gate. Do not enter Sprint 004 until human review approves.

## Notes

- Legacy UI remains default: `python -m nfs_scanner.main`
- Commercial UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`
- RealtimeCanvas mock layers unchanged (photo, heatmap, path, marker, ColorBar, MiniMap).
- `config/instrument_devices.json` is runtime cache; example template is `config/instrument_devices.example.json`.
- No real device, scan runtime, or CSV format changes.

## Next Recommended

- Human review of Sprint 003 visual consistency
- Optional: migrate remaining commercial views to explicit NFSCard imports
- Sprint 004 planning after review approval
