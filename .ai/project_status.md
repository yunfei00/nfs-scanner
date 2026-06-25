# Project Status

Last updated: 2026-06-25

## Current Mode

**STOP — Major Review Gate (post Sprint 010 Real Integration Preparation)**

Major Review Gate（接入前）已通过；**真实设备控制尚未批准**。

## Sprint Progress

| Sprint | Status | Notes |
|--------|--------|-------|
| Sprint 001–009 | done | Shell through Data View Mock |
| Sprint 010 | done | Real Integration Preparation (protocols + safety) |
| Real Device Control | **blocked** | Requires separate Major Review |

## Next Actions (Human)

1. Review `.ai/daily/2026-06-25-sprint010-real-integration-prep.md`
2. Approve or redirect before **Real Device Control Sprint**
3. Verify commercial UI still runs with mock services

## Application Entry Points

- Legacy UI (default): `python -m nfs_scanner.main`
- Commercial UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`

## Recent Capabilities (Sprint 010)

- `ScanRuntimeServiceProtocol` / `DeviceServiceProtocol` — UI-agnostic contracts
- `MockScanRuntimeService` + `MockDeviceService` — default commercial implementations
- `CommercialServiceBundle` — centralized service injection in `entry.py`
- `integration_safety.py` — `REAL_DEVICE_ENABLED=false`; toolbar real-device entry disabled

## Constraints (unchanged)

- No real device motion commands, spectrum, or camera until explicitly approved.
- No CSV format changes. Old UI must remain available.
