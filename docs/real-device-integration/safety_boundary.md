# Safety Boundary

1. `NFS_SCANNER_REAL_DEVICES=1` required for any real I/O
2. `SafetyGate` + `require_real_device_control()` — never bypass
3. Connect does not move axes
4. Scan requires explicit UI confirmation
5. Automated tests use fake transports only
