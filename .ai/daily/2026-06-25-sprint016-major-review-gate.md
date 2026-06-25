# Sprint 016 — Major Review Gate (Before Real Motion Control)

Date: 2026-06-25

## Status: **STOP — Awaiting Human Approval for Real Motion Control**

Sprint 015 complete. Real serial **connection test** only — **no motion commands** were sent.

---

## What Was Built (Sprint 015)

| Component | Purpose |
|-----------|---------|
| `MotionDeviceConfig.connection_mode` | `mock` (default) vs `real_connection_test` |
| `serial_discovery.list_serial_ports()` | Optional pyserial; empty list if unavailable |
| `MotionConnectionAdapter` | Serial open/close only; forbids home/jog/move/write |
| Device Center motion UI | Port picker, banner `REAL CONNECTION TEST - NO MOTION` |

---

## Safety Checklist

- [x] No G0/G1/$H/unlock/reset or any write to serial for motion
- [x] `require_real_device_control()` on real open
- [x] Default `connection_mode=mock`
- [x] No spectrum/camera/scan/CSV changes
- [x] Legacy UI untouched
- [x] 127 tests passing

---

## Manual Real Connection Test (optional)

```powershell
$env:NFS_SCANNER_REAL_DEVICES="1"
$env:NFS_SCANNER_UI="commercial"
python -m nfs_scanner.main
```

Device Center → 运动平台 → `real_connection_test` → 选择串口 → 连接/断开。

**Still no motion commands** even with env enabled.

---

## Next Step (after approval)

Real Motion Control Sprint — jog/home/move behind separate Major Review and additional guards.

---

## Autopilot Stop

Do not auto-start real motion control.
