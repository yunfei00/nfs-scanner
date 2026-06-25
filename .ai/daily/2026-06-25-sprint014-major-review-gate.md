# Sprint 014 — Major Review Gate (Before Real Hardware Control)

Date: 2026-06-25

## Status: **STOP — Awaiting Human Approval for Real Device Control**

Sprints 011–013 complete. **Do not** enable real motion, spectrum, camera, or ScanManager integration until explicitly approved.

---

## Completed Since Sprint 010

| Sprint | Theme | Highlights |
|--------|-------|------------|
| 011 | Device Center UX | Full mock device page; sidebar summary sync |
| 012 | Device Config Models | Validated dataclasses; in-memory mock config UI |
| 013 | Dry Run Command Layer | Log-only adapters; mock scan emits dry-run trace |

---

## Safety Checklist

- [x] `REAL_DEVICE_ENABLED = false` (default)
- [x] `NFS_SCANNER_REAL_DEVICES` not required for mock/dry-run
- [x] Toolbar「连接设备」disabled unless env explicitly enabled
- [x] Dry-run adapters never open serial/VISA/camera
- [x] No `ScanManager` integration
- [x] No CSV / format changes
- [x] Legacy UI unchanged
- [x] 112 unit tests passing

---

## Architecture Ready For (not implemented)

- Swap `MockDeviceService` → `RealDeviceService` behind protocol
- Swap dry-run adapters → real adapters after `require_real_device_control()`
- Bridge `ScanRuntimeServiceProtocol` → future real runtime

---

## Recommended Next Step (after approval)

**Real Device Control Sprint** — motion-only mock serial bridge or read-only device status first, with feature flag and separate Major Review per device class.

---

## Autopilot Stop

**Major Review Gate reached.** Do not auto-start real hardware control.
