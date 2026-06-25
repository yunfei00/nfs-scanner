# Commercial UI Visual Report

- Generated: 2026-06-26 07:23:08
- Default screenshot: `D:/code_2026/nfs-scanner/.ai/visual_check/commercial_default.png`
- Maximized screenshot: `D:/code_2026/nfs-scanner/.ai/visual_check/commercial_maximized.png`

## Default Window

**Result: PASS**

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| custom_title_bar | frameless + title bar visible | custom=True, height=34px | PASS |
| title_bar_height | 28–44 px | 34px | PASS |
| bottom_dock_height | >= 195 px | 195px | PASS |
| log_view_height | >= 100 px | 111px | PASS |
| statistics_panel_height | >= 100 px | 149px | PASS |
| canvas_size | height >= 240px | 636x307px | PASS |
| colorbar_adjacent | gap <= 12 px | 2px | PASS |
| right_panel_width | 300–380 px | 320px | PASS |
| left_panel_width | 220–280 px | 240px | PASS |
| center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.99x, left=2.65x, area=81% | PASS |
| workspace_wider_than_right_panel | workspace > right panel | 696px > 320px | PASS |
| toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| status_bar_visible | status bar visible | True | PASS |
| default_window_within_screen | window <= available screen | 1280x720 <= 1280x720 | PASS |

## Scrollbar / Slider Usability (Default)

**Result: PASS**

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| qss_scrollbar_handle_min_height | >= 48px in QSS | 48px | PASS |
| qss_scrollbar_handle_min_width | >= 48px in QSS | 48px | PASS |
| left_scrollbar_width | >= 12px when visible | 14px | PASS |
| property_scrollbar_width | >= 12px when visible | 14px | PASS |
| log_scrollbar_width | >= 12px when scrollable | 14px | PASS |
| log_area_scrollable | log content scrollable | range=11 | PASS |
| property_area_scrollable | property panel scrollable | range=699 | PASS |
| device_status_scrollable_or_compact | device scroll visible when needed | width=14px | PASS |
| wheel_interaction | wheel step changes scroll value | True | PASS |
| handle_position_interaction | handle position can be set smoothly | True | PASS |

### Manual Behavior Verification

- 滚轮测试: PASS
- Scrollbar handle 拖动测试: PASS
- Slider 拖动测试: Not Applicable

## Maximized Window

**Result: PASS**

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| custom_title_bar | frameless + title bar visible | custom=True, height=34px | PASS |
| title_bar_height | 28–44 px | 34px | PASS |
| bottom_dock_height | >= 195 px | 195px | PASS |
| log_view_height | >= 100 px | 111px | PASS |
| statistics_panel_height | >= 100 px | 149px | PASS |
| canvas_size | height >= 240px | 636x307px | PASS |
| colorbar_adjacent | gap <= 12 px | 2px | PASS |
| right_panel_width | 300–380 px | 320px | PASS |
| left_panel_width | 220–280 px | 240px | PASS |
| center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.99x, left=2.65x, area=81% | PASS |
| workspace_wider_than_right_panel | workspace > right panel | 696px > 320px | PASS |
| toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| status_bar_visible | status bar visible | True | PASS |
| maximized_window | custom maximized == True | True | PASS |

## Overall: PASS
