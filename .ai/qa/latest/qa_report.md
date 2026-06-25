# Commercial Demo QA Report

- Generated: 2026-06-26 07:14:35
- Round: 1
- Overall: **PASS**

## Screenshots

- `commercial_default`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/commercial_default.png`
- `realtime_view`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/realtime_view.png`
- `device_center`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/device_center.png`
- `data_view`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/data_view.png`
- `report_center`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/report_center.png`
- `commercial_maximized`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/commercial_maximized.png`

## Startup — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| legacy_ui_startup | MainWindow constructs and shows | MainWindow | PASS |
| commercial_ui_startup | CommercialMainShell constructs with custom title bar | visible=True, custom_title=True | PASS |

## Visual — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| custom_title_bar | frameless custom title bar | custom=True, height=34px | PASS |
| no_native_title_bar | FramelessWindowHint enabled | custom=True | PASS |
| title_bar_height | 28–44 px | 34px | PASS |
| demo_indicator_visible | demo banner or DEMO MODE label visible | title bar demo label: DEMO MODE | PASS |
| toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| left_panel_width | 220–280 px | 240px | PASS |
| right_panel_width | 300–380 px | 320px | PASS |
| center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.99x, left=2.65x, area=81% | PASS |
| canvas_wider_than_right_panel | workspace > right panel | 696px > 320px | PASS |
| bottom_dock_height | >= 195px | 195px | PASS |
| log_view_height | >= 100px | 111px | PASS |
| log_visible_lines | >= 6 visible lines | estimated=8 | PASS |
| statistics_panel_height | >= 100px | 149px | PASS |
| status_bar_visible | status bar visible | True | PASS |
| default_window_within_screen | window <= available screen | 1280x720 <= 1280x720 | PASS |
| maximized_custom_title_bar | frameless custom title bar | custom=True, height=34px | PASS |
| maximized_no_native_title_bar | FramelessWindowHint enabled | custom=True | PASS |
| maximized_title_bar_height | 28–44 px | 34px | PASS |
| maximized_demo_indicator_visible | demo banner or DEMO MODE label visible | title bar demo label: DEMO MODE | PASS |
| maximized_toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| maximized_left_panel_width | 220–280 px | 240px | PASS |
| maximized_right_panel_width | 300–380 px | 320px | PASS |
| maximized_center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.99x, left=2.65x, area=81% | PASS |
| maximized_canvas_wider_than_right_panel | workspace > right panel | 696px > 320px | PASS |
| maximized_bottom_dock_height | >= 195px | 195px | PASS |
| maximized_log_view_height | >= 100px | 111px | PASS |
| maximized_log_visible_lines | >= 6 visible lines | estimated=6 | PASS |
| maximized_statistics_panel_height | >= 100px | 149px | PASS |
| maximized_status_bar_visible | status bar visible | True | PASS |
| maximized_maximized_window_capture | custom maximized == True | True | PASS |

## Functional — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| new_project_updates_status | project label reflects new session | 项目: Demo Near Field Scan (未保存) | PASS |
| open_mock_project_updates_status | project label reflects mock project | 项目: Demo Near Field Scan (未保存) | PASS |
| save_project_updates_storage | storage status shows saved | 项目: Demo Near Field Scan (已保存) | PASS |
| mock_connect_devices | all mock devices connected | 相机, 运动平台, 频谱仪 | PASS |
| scan_params_update_preview_stats | preview point count updates | before=441, after=9 | PASS |
| start_scan_running | runtime status == running | running | PASS |
| pause_scan_paused | runtime status == paused | paused | PASS |
| resume_scan_running | runtime status == running | running | PASS |
| scan_completes_or_stops | runtime status completed or stopped | completed | PASS |
| data_view_mock_task | data view lists mock scan tasks | 4 | PASS |
| report_center_preview | report preview populated | Demo Near Field Scan | PASS |
| mock_report_export | markdown/txt report file created | C:\Users\yunfei\.nfs_scanner\reports\report_mock-4f3cdae0_20260626_071436.md | PASS |
| reset_demo_restores_state | runtime idle and demo reset applied | status=stopped, tasks 4->2 | PASS |

## Safety — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| real_device_enabled_false | REAL_DEVICE_ENABLED == False | False | PASS |
| real_devices_env_not_set | NFS_SCANNER_REAL_DEVICES not enabled | (unset) | PASS |
| real_device_control_not_allowed | is_real_device_control_allowed() == False | False | PASS |
| commercial_shell_no_scan_manager | Commercial main shell does not import ScanManager | not referenced | PASS |
| mock_runtime_no_scan_manager | Mock runtime does not use ScanManager | not referenced | PASS |
| legacy_ui_entry_preserved | Legacy MainWindow source exists | D:\code_2026\nfs-scanner\nfs_scanner\ui\main_window.py | PASS |
| legacy_default_entry | Default startup uses MainWindow unless NFS_SCANNER_UI=commercial | is_commercial_ui_enabled | PASS |
| dry_run_no_real_motion_commands | Dry run log contains DRY RUN markers, no real G-code | forbidden hits=none, lines=21 | PASS |
| no_real_spectrum_connection | No real spectrum connection attempts | none | PASS |
| no_real_camera_connection | No real camera connection attempts | none | PASS |

## External — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| compileall | exit code 0 | Listing 'nfs_scanner\\ui\\widgets'... | PASS |
| unittest | exit code 0 | OK | PASS |
| commercial_ui_visual_check | exit code 0 | Overall: PASS | PASS |

## Failures

- none

## Known Issues

- none
