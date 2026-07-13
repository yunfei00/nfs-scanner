# Commercial Demo QA Report

- Generated: 2026-07-13 23:07:40
- Round: 1
- Overall: **PASS**

## Screenshots

- (none)

## Safety — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| real_device_enabled_false | REAL_DEVICE_ENABLED == False | False | PASS |
| real_devices_env_not_set | NFS_SCANNER_REAL_DEVICES not enabled | (unset) | PASS |
| real_device_control_not_allowed | is_real_device_control_allowed() == False | False | PASS |
| commercial_shell_no_scan_manager | Commercial main shell does not import ScanManager | not referenced | PASS |
| mock_runtime_no_scan_manager | Mock runtime does not use ScanManager | not referenced | PASS |
| legacy_ui_entry_preserved | Legacy MainWindow source exists | D:\code_2026\nfs-scanner\nfs_scanner\ui\main_window.py | PASS |
| commercial_default_entry | Default startup uses CommercialMainShell; NFS_SCANNER_UI=legacy keeps MainWindow | commercial gate present | PASS |

## External — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| compileall | exit code 0 and no unapproved exception markers | Listing 'nfs_scanner\\ui\\widgets'... | PASS |
| unittest | exit code 0 and no unapproved exception markers | OK (skipped=25) | PASS |
| commercial_ui_visual_check | exit code 0 and no unapproved exception markers | SKIP: headless environment (set DISPLAY or unset NFS_SCANNER_SKIP_GUI_TESTS) | PASS |

## Failures

- none

## Known Issues

- GUI checks skipped in headless environment
