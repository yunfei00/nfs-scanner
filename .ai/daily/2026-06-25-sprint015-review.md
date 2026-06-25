# Sprint 015 Review — Motion Device Connection Only

Date: 2026-06-25

## Delivered

- `MotionDeviceConfig`: timeout, connection_mode (`mock` / `real_connection_test`)
- `list_serial_ports()` optional pyserial discovery
- `MotionConnectionAdapter`: open/close only, no motion commands
- Device Center: port/baud/mode UI, connection log, sidebar sync
- Safety: `NFS_SCANNER_REAL_DEVICES=1` required for real serial open

## Verification

- [x] `python -m unittest discover -s tests -v` (127 tests OK)
- [x] No home/jog/move/G-code commands
- [x] Mock mode unchanged

## Soft Review Gate

Stop at Sprint 016 Major Review Gate before real motion control.
