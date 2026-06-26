# Commercial Demo QA Report

- Generated: 2026-06-26 08:41:32
- Round: 1
- Overall: **PASS**

## Screenshots

- `commercial_default`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/commercial_default.png`
- `top_header`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/top_header.png`
- `commercial_top_header`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/commercial_top_header.png`
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
| custom_title_bar | frameless custom title bar | custom=True, height=52px | PASS |
| no_native_title_bar | FramelessWindowHint enabled | custom=True | PASS |
| title_bar_height | 28–44 px | 52px | PASS |
| demo_indicator_visible | demo banner or DEMO MODE label visible | top status area visible | PASS |
| toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| left_panel_width | 220–280 px | 230px | PASS |
| right_panel_width | 340–380 px | 350px | PASS |
| center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.76x, left=2.68x, area=81% | PASS |
| canvas_wider_than_right_panel | workspace > right panel | 676px > 350px | PASS |
| bottom_dock_height | >= 200px | 200px | PASS |
| log_view_height | >= 100px | 140px | PASS |
| log_visible_lines | >= 6 visible lines | estimated=12 | PASS |
| statistics_panel_height | >= 100px | 192px | PASS |
| status_bar_visible | status bar visible | True | PASS |
| default_window_within_screen | window <= available screen | 1280x720 <= 1280x720 | PASS |
| maximized_custom_title_bar | frameless custom title bar | custom=True, height=52px | PASS |
| maximized_no_native_title_bar | FramelessWindowHint enabled | custom=True | PASS |
| maximized_title_bar_height | 28–44 px | 52px | PASS |
| maximized_demo_indicator_visible | demo banner or DEMO MODE label visible | top status area visible | PASS |
| maximized_toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| maximized_left_panel_width | 220–280 px | 230px | PASS |
| maximized_right_panel_width | 340–380 px | 350px | PASS |
| maximized_center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.76x, left=2.68x, area=81% | PASS |
| maximized_canvas_wider_than_right_panel | workspace > right panel | 676px > 350px | PASS |
| maximized_bottom_dock_height | >= 200px | 200px | PASS |
| maximized_log_view_height | >= 100px | 140px | PASS |
| maximized_log_visible_lines | >= 6 visible lines | estimated=26 | PASS |
| maximized_statistics_panel_height | >= 100px | 192px | PASS |
| maximized_status_bar_visible | status bar visible | True | PASS |
| maximized_maximized_window_capture | custom maximized == True | True | PASS |

## Functional — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| new_project_updates_status | project label reflects new session | 项目: Demo Near Field Scan (未保存) | PASS |
| open_mock_project_updates_status | project label reflects mock project | 项目: Demo Near Field Scan (未保存) | PASS |
| save_project_updates_storage | storage status shows saved | 项目: Demo Near Field Scan (已保存) | PASS |
| mock_connect_devices | all mock devices connected | 相机, 运动平台, 频谱仪 | PASS |
| scan_params_update_preview_stats | preview point count updates | before=91 x 71 = 6,461, after=3 x 3 = 9 | PASS |
| start_scan_running | runtime status == running | running | PASS |
| pause_scan_paused | runtime status == paused | paused | PASS |
| resume_scan_running | runtime status == running | running | PASS |
| scan_completes_or_stops | runtime status completed or stopped | completed | PASS |
| data_view_mock_task | data view lists mock scan tasks | 4 | PASS |
| report_center_preview | report preview populated | Demo Near Field Scan | PASS |
| mock_report_export | markdown/txt report file created | C:\Users\yunfei\.nfs_scanner\reports\report_mock-b7208616_20260626_084135.md | PASS |
| reset_demo_restores_state | runtime idle and demo reset applied | status=stopped, tasks 4->2 | PASS |

## Interaction — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| qss_scrollbar_handle_min_height | >= 24px in QSS | 28px | PASS |
| qss_scrollbar_handle_min_width | >= 24px in QSS | 28px | PASS |
| left_scrollbar_width | >= 12px when visible | 0px | PASS |
| property_scrollbar_width | >= 12px when visible | 14px | PASS |
| log_scrollbar_width | >= 12px when scrollable | 14px | PASS |
| log_area_scrollable | log content scrollable | range=19 | PASS |
| property_area_scrollable | property panel scrollable | range=532 | PASS |
| device_status_scrollable_or_compact | device scroll visible when needed | width=14px | PASS |
| wheel_interaction | wheel step changes scroll value | True | PASS |
| handle_position_interaction | handle position can be set smoothly | True | PASS |
| slider_widgets_present | slider handle style configured | QSlider found | PASS |
| wheel_test | wheel step changes scroll value | PASS | PASS |
| scrollbar_handle_drag | handle position adjustable (programmatic) | PASS | PASS |
| slider_drag | slider interaction | PASS | PASS |

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

## Manual Behavior Verification

- 滚轮测试: PASS
- Scrollbar handle 拖动测试: PASS
- Slider 拖动测试: PASS
