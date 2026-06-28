# Commercial Demo QA Report

- Generated: 2026-06-28 22:10:03
- Round: 1
- Overall: **PASS**

## Screenshots

- `commercial_default`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/commercial_default.png`
- `top_header`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/top_header.png`
- `commercial_top_header`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/commercial_top_header.png`
- `realtime_view`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/realtime_view.png`
- `realtime_view_final`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/realtime_view_final.png`
- `device_center`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/device_center.png`
- `device_center_final`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/device_center_final.png`
- `data_view`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/data_view.png`
- `data_view_final`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/data_view_final.png`
- `report_center`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/report_center.png`
- `report_center_final`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/report_center_final.png`
- `three_d_view`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/three_d_view.png`
- `three_d_view_final`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/three_d_view_final.png`
- `data_table`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/data_table.png`
- `data_table_final`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/data_table_final.png`
- `display_settings_final`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/display_settings_final.png`
- `instrument_settings_final`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/instrument_settings_final.png`
- `self_check_final`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/self_check_final.png`
- `reset_demo`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/reset_demo_final.png`
- `stopped_scan`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/stopped_scan.png`
- `reset_after_report`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/reset_after_report.png`
- `button_state_matrix`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/button_state_matrix.png`
- `commercial_maximized`: `D:/code_2026/nfs-scanner/.ai/qa/latest/screenshots/commercial_maximized.png`

## Startup — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| legacy_ui_startup | MainWindow constructs and shows | MainWindow | PASS |
| commercial_ui_startup | CommercialMainShell constructs with custom title bar | visible=True, custom_title=True | PASS |

## Visual — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| top_header_screenshot_exists | top_header.png exists | True | PASS |
| custom_title_bar | frameless custom title bar | custom=True, height=54px | PASS |
| no_native_title_bar | FramelessWindowHint enabled | custom=True | PASS |
| title_bar_height | 48–58 px | 54px | PASS |
| demo_indicator_visible | demo banner or DEMO MODE label visible | top status area visible | PASS |
| toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| left_panel_width | 220–280 px | 230px | PASS |
| right_panel_width | 340–380 px | 350px | PASS |
| center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.76x, left=2.68x, area=81% | PASS |
| canvas_wider_than_right_panel | workspace > right panel | 676px > 350px | PASS |
| bottom_dock_height | >= 200px | 200px | PASS |
| log_view_height | >= 100px | 140px | PASS |
| log_visible_lines | >= 6 visible lines | estimated=13 | PASS |
| statistics_panel_height | >= 100px | 192px | PASS |
| status_bar_visible | status bar visible | True | PASS |
| default_window_within_screen | window <= available screen | 1280x720 <= 1280x720 | PASS |
| reset_demo_screenshot_exists | reset_demo.png exists | True | PASS |
| maximized_custom_title_bar | frameless custom title bar | custom=True, height=54px | PASS |
| maximized_no_native_title_bar | FramelessWindowHint enabled | custom=True | PASS |
| maximized_title_bar_height | 48–58 px | 54px | PASS |
| maximized_demo_indicator_visible | demo banner or DEMO MODE label visible | top status area visible | PASS |
| maximized_toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| maximized_left_panel_width | 220–280 px | 230px | PASS |
| maximized_right_panel_width | 340–380 px | 350px | PASS |
| maximized_center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.76x, left=2.68x, area=81% | PASS |
| maximized_canvas_wider_than_right_panel | workspace > right panel | 676px > 350px | PASS |
| maximized_bottom_dock_height | >= 200px | 200px | PASS |
| maximized_log_view_height | >= 100px | 140px | PASS |
| maximized_log_visible_lines | >= 6 visible lines | estimated=103 | PASS |
| maximized_statistics_panel_height | >= 100px | 192px | PASS |
| maximized_status_bar_visible | status bar visible | True | PASS |
| maximized_maximized_window_capture | custom maximized == True | True | PASS |

## Functional — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| new_project_updates_status | project label reflects new session | 项目: FunctionalNewProject | PASS |
| open_mock_project_updates_status | project label reflects mock project | 项目: Demo Near Field Scan | PASS |
| save_project_updates_storage | storage status shows saved | 项目: Demo Near Field Scan | PASS |
| mock_connect_devices | all mock devices connected | 相机, 运动平台, 频谱仪, VNA / Trace Source | PASS |
| scan_params_update_preview_stats | preview point count updates | before=91 x 71 = 6,461, after=3 x 3 = 9 | PASS |
| start_scan_running | runtime status == running | running | PASS |
| scan_progress_above_5_percent | progress > 5% | 11% | PASS |
| workflow_scan_step_active | workflow step 5 active while scanning | 4 | PASS |
| pause_scan_paused | runtime status == paused | paused | PASS |
| resume_scan_running | runtime status == running | running | PASS |
| scan_progress_increases_after_resume | progress increases after resume | before=22%, after=33% | PASS |
| stop_scan_stopped | runtime status == stopped | stopped | PASS |
| scan_completes_or_stops | runtime status completed or stopped | completed | PASS |
| data_view_mock_task | data view lists mock scan tasks | 3 | PASS |
| data_view_export_mock_json | data export creates mock json | C:\Users\yunfei\.nfs_scanner\mock_exports\data\mock_data_demo_mock-3e538069_20260628_221008.json | PASS |
| report_center_preview | report preview populated | Demo Near Field Scan | PASS |
| mock_report_export | markdown/txt report file created | C:\Users\yunfei\.nfs_scanner\reports\report_mock-3e538069_20260628_221008.md | PASS |
| mock_report_multi_format_export | html/pdf/png mock report files created | .html, .pdf, .png | PASS |
| mock_self_check_report | local mock self-check report created | .ai\qa\latest\commercial_mock_self_check.json | PASS |
| reset_demo_restores_state | runtime idle and demo reset applied | status=configured, tasks 3->2 | PASS |

## Mock_Features — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| toolbar_photo_feedback | snapshot path logged | True | PASS |
| toolbar_region_align | region aligned | True | PASS |
| toolbar_clear_overlay | clear overlays invoked | ok | PASS |
| property_scan_template | scan template applied | 快速扫描 | PASS |
| property_instrument_config | instrument config saved | saved | PASS |
| tab_three_d_view_non_empty | view has content | three_d_view | PASS |
| tab_data_table_view_non_empty | view has content | data_table_view | PASS |
| display_opacity_applied | opacity changed | 45 | PASS |
| data_table_csv_export | csv export path emitted | exported | PASS |
| report_center_preview_available | preview populated | Demo Near Field Scan | PASS |
| self_check_runnable | self check json exists | .ai/qa/latest/commercial_mock_self_check.json | PASS |
| functional_mock_features | scan completes after mock feature checks | completed | PASS |
| all_visible_actions_have_feedback | toolbar actions tested | 12 | PASS |
| all_tabs_non_empty | 3d and table checked | ok | PASS |
| all_exports_created | photo + table export | ok | PASS |

## Interaction — PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| qss_scrollbar_handle_min_height | >= 24px in QSS | 28px | PASS |
| qss_scrollbar_handle_min_width | >= 24px in QSS | 28px | PASS |
| left_scrollbar_width | >= 12px when visible | 14px | PASS |
| property_scrollbar_width | >= 12px when visible | 14px | PASS |
| log_scrollbar_width | >= 12px when scrollable | 14px | PASS |
| log_area_scrollable | log content scrollable | range=98 | PASS |
| property_area_scrollable | property panel scrollable | range=176 | PASS |
| device_status_scrollable_or_compact | device scroll visible when needed | width=0px | PASS |
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
