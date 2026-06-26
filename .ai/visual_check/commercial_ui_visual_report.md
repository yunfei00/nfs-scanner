# Commercial UI Visual Report

- Generated: 2026-06-26 08:30:03
- Default screenshot: `D:/code_2026/nfs-scanner/.ai/visual_check/commercial_default.png`
- Top header screenshot: `D:/code_2026/nfs-scanner/.ai/visual_check/commercial_top_header.png`
- Maximized screenshot: `D:/code_2026/nfs-scanner/.ai/visual_check/commercial_maximized.png`

## Default Window

**Result: PASS**

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| custom_title_bar | frameless + title bar visible | custom=True, height=36px | PASS |
| title_bar_height | 28–44 px | 36px | PASS |
| bottom_dock_height | >= 200 px | 200px | PASS |
| log_view_height | >= 100 px | 140px | PASS |
| statistics_panel_height | >= 100 px | 192px | PASS |
| canvas_size | height >= 240px | 616x366px | PASS |
| colorbar_adjacent | gap <= 12 px | 2px | PASS |
| right_panel_width | 340–380 px | 350px | PASS |
| left_panel_width | 220–280 px | 230px | PASS |
| center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.76x, left=2.68x, area=82% | PASS |
| workspace_wider_than_right_panel | workspace > right panel | 676px > 350px | PASS |
| toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| status_bar_visible | status bar visible | True | PASS |
| default_window_within_screen | window <= available screen | 1280x720 <= 1280x720 | PASS |
| top_header_integrated | toolbar embedded in unified top header | header=True, parent=commercialTopHeader | PASS |
| brand_single_line_row | brand title/subtitle/version on one horizontal row | row=True, single_line=True | PASS |
| target_style_mode | targetStyleMode enabled | true | PASS |
| logo_area_exists | NFS logo block visible | visible=True | PASS |
| top_toolbar_icon_mode | >= 12 toolbar actions | 13 | PASS |
| workflow_timeline_mode | >= 7 timeline steps | 7 | PASS |
| right_compact_grid_form | property tabs + xyz grid rows | tabs=True, rows=3 | PASS |
| bottom_dock_three_panel_mode | tri-panel dock visible | visible=True | PASS |
| spectrum_panel_visible | spectrum panel visible | visible=True | PASS |
| spectrum_yellow_curve_mode | yellow curve spectrum widget | true | PASS |
| scan_stats_panel_visible | scan stats panel visible | visible=True | PASS |
| scan_stats_demo_values | seeded runtime stat values | 2.450 GHz | PASS |
| log_panel_visible | log panel visible with >= 6 lines | lines=12 | PASS |
| log_category_tags | INFO/WARN/ERROR/SCAN/DATA tags | True | PASS |
| pcb_like_mock_board | photo layer mock board loaded | photo_layer_ready | PASS |
| heatmap_smooth_mode | heatmap overlay enabled | 1 | PASS |
| roi_control_points_visible | ROI overlay items present | 9 | PASS |
| right_panel_no_horizontal_clip | property panel fits viewport width | True | PASS |
| scan_progress_bar_visible | runtime progress bar in dock | visible=True | PASS |
| canvas_axis_legend | axis legend visible | visible=True | PASS |
| canvas_cursor_hud | cursor HUD visible | visible=True | PASS |
| minimap_title_visible | MiniMap title "全局视图" | 全局视图 | PASS |

## Scrollbar / Slider Usability (Default)

**Result: PASS**

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| qss_scrollbar_handle_min_height | >= 24px in QSS | 28px | PASS |
| qss_scrollbar_handle_min_width | >= 24px in QSS | 28px | PASS |
| left_scrollbar_width | >= 12px when visible | 0px | PASS |
| property_scrollbar_width | >= 12px when visible | 14px | PASS |
| log_scrollbar_width | >= 12px when scrollable | 14px | PASS |
| log_area_scrollable | log content scrollable | range=5 | PASS |
| property_area_scrollable | property panel scrollable | range=516 | PASS |
| device_status_scrollable_or_compact | device scroll visible when needed | width=14px | PASS |
| wheel_interaction | wheel step changes scroll value | True | PASS |
| handle_position_interaction | handle position can be set smoothly | True | PASS |
| slider_widgets_present | slider handle style configured | QSlider found | PASS |

### Manual Behavior Verification

- 滚轮测试: PASS
- Scrollbar handle 拖动测试: PASS
- Slider 拖动测试: PASS

## Maximized Window

**Result: PASS**

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| custom_title_bar | frameless + title bar visible | custom=True, height=36px | PASS |
| title_bar_height | 28–44 px | 36px | PASS |
| bottom_dock_height | >= 200 px | 200px | PASS |
| log_view_height | >= 100 px | 140px | PASS |
| statistics_panel_height | >= 100 px | 192px | PASS |
| canvas_size | height >= 240px | 616x366px | PASS |
| colorbar_adjacent | gap <= 12 px | 2px | PASS |
| right_panel_width | 340–380 px | 350px | PASS |
| left_panel_width | 220–280 px | 230px | PASS |
| center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.76x, left=2.68x, area=82% | PASS |
| workspace_wider_than_right_panel | workspace > right panel | 676px > 350px | PASS |
| toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| status_bar_visible | status bar visible | True | PASS |
| maximized_window | custom maximized == True | True | PASS |
| top_header_integrated | toolbar embedded in unified top header | header=True, parent=commercialTopHeader | PASS |
| brand_single_line_row | brand title/subtitle/version on one horizontal row | row=True, single_line=True | PASS |
| target_style_mode | targetStyleMode enabled | true | PASS |
| logo_area_exists | NFS logo block visible | visible=True | PASS |
| top_toolbar_icon_mode | >= 12 toolbar actions | 13 | PASS |
| workflow_timeline_mode | >= 7 timeline steps | 7 | PASS |
| right_compact_grid_form | property tabs + xyz grid rows | tabs=True, rows=3 | PASS |
| bottom_dock_three_panel_mode | tri-panel dock visible | visible=True | PASS |
| spectrum_panel_visible | spectrum panel visible | visible=True | PASS |
| spectrum_yellow_curve_mode | yellow curve spectrum widget | true | PASS |
| scan_stats_panel_visible | scan stats panel visible | visible=True | PASS |
| scan_stats_demo_values | seeded runtime stat values | 2.450 GHz | PASS |
| log_panel_visible | log panel visible with >= 6 lines | lines=12 | PASS |
| log_category_tags | INFO/WARN/ERROR/SCAN/DATA tags | True | PASS |
| pcb_like_mock_board | photo layer mock board loaded | photo_layer_ready | PASS |
| heatmap_smooth_mode | heatmap overlay enabled | 1 | PASS |
| roi_control_points_visible | ROI overlay items present | 9 | PASS |
| right_panel_no_horizontal_clip | property panel fits viewport width | True | PASS |
| scan_progress_bar_visible | runtime progress bar in dock | visible=True | PASS |
| canvas_axis_legend | axis legend visible | visible=True | PASS |
| canvas_cursor_hud | cursor HUD visible | visible=True | PASS |
| minimap_title_visible | MiniMap title "全局视图" | 全局视图 | PASS |

## Overall: PASS
