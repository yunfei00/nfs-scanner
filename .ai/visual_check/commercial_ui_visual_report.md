# Commercial UI Visual Report

- Generated: 2026-06-26 21:33:28
- Default screenshot: `D:/code_2026/nfs-scanner/.ai/visual_check/commercial_default.png`
- Top header screenshot: `D:/code_2026/nfs-scanner/.ai/visual_check/commercial_top_header.png`
- Maximized screenshot: `D:/code_2026/nfs-scanner/.ai/visual_check/commercial_maximized.png`

## Default Window

**Result: PASS**

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| custom_title_bar | frameless + title bar visible | custom=True, height=54px | PASS |
| title_bar_height | 48–58 px | 54px | PASS |
| bottom_dock_height | >= 200 px | 200px | PASS |
| log_view_height | >= 100 px | 140px | PASS |
| statistics_panel_height | >= 100 px | 192px | PASS |
| canvas_size | height >= 240px | 616x348px | PASS |
| colorbar_adjacent | gap <= 12 px | 2px | PASS |
| right_panel_width | 340–380 px | 350px | PASS |
| left_panel_width | 220–280 px | 230px | PASS |
| workflow_panel_height | <= 360 px | 257px | PASS |
| device_status_panel_height | expanded content height 120-650 px in left scroll | 624px | PASS |
| left_no_nested_device_scroll | no isolated device-status scroll area | inner_scroll=False | PASS |
| device_status_collapsed_height | collapsed height <= 100 px | 45px | PASS |
| property_tab_bar_fixed | tab bar visible after content scroll | True | PASS |
| numeric_field_line_edit_width | >= 48 px | 52px | PASS |
| numeric_field_total_width | >= 80 px | 80px | PASS |
| scan_action_buttons_layout | start/pause/stop present with no overlap or clipping | count=3, overlap=False, clipped=False | PASS |
| realtime_toolbar_button_text | no "..." labels and width >= 44 px | min_width=52px, ellipsis=False | PASS |
| lut_combo_common_presets | realtime and display LUT combos include Jet/common presets | count=3, include_common=True | PASS |
| center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.76x, left=2.68x, area=81% | PASS |
| workspace_wider_than_right_panel | workspace > right panel | 676px > 350px | PASS |
| toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| status_bar_visible | status bar visible | True | PASS |
| default_window_within_screen | window <= available screen | 1280x720 <= 1280x720 | PASS |
| target_style_mode | targetStyleMode enabled | true | PASS |
| logo_area_exists | NFS logo block visible | visible=True | PASS |
| top_toolbar_icon_mode | >= 12 toolbar actions | 13 | PASS |
| workflow_timeline_mode | >= 7 timeline steps | 7 | PASS |
| right_compact_grid_form | property tabs + scan region grid/table | tabs=True, rows=1 | PASS |
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
| header_matches_target_mode | targetStyleMode enabled on shell and toolbar | shell=true, toolbar=true | PASS |
| overflow_hidden_at_default_width | overflow hidden when width >= 1500px | width=1280px, overflow=True | PASS |
| toolbar_separator_count_reasonable | strong separators <= 4 | 4 | PASS |
| toolbar_button_width_reasonable | visible buttons width >= 56px | min=60px | PASS |
| toolbar_no_text_touching | adjacent buttons gap >= 4px | count=10, min_gap>=4px | PASS |
| brand_logo_exists | NFS logo square >= 40px | logo=True, size=44x44 | PASS |
| brand_logo_widget_used | NFSLogoWidget or brandLogoWidget property | widget=True, prop=True | PASS |
| brand_logo_not_plain_label | logo is not a plain QLabel text block | plain_label=False | PASS |
| toolbar_custom_icons_used | all toolbar buttons use customToolIcon | custom=13/13 | PASS |
| toolbar_no_qt_default_icon_mode | Qt standard icons not used for toolbar actions | True | PASS |
| auth_status_lightweight | lightweight auth label, not large chip | label_hint=84x16 | PASS |
| brand_logo_blue_enough | brandLogoBlue property on logo tile | brandLogoBlue=True | PASS |
| brand_logo_blue_block | blue brand logo block, not flat black | brandBlueBlock=True | PASS |
| brand_title_hierarchy | CN title + EN subtitle + version badge | title=True, subtitle=True, badge=True, hierarchy=True | PASS |
| brand_not_flat_text | brand is not a single flat text row | flat=False | PASS |
| version_badge_exists | v* version badge visible | v1.0.0 | PASS |
| top_header_height_consistent | 48–58px | 54px | PASS |
| toolbar_button_text_not_overlapping | visible toolbar buttons do not overlap | count=10, min_gap>=2px | PASS |
| toolbar_caption_readable | short readable captions, width >= 56px | count=10, width=60px | PASS |
| toolbar_icon_mode | icon-above-text tool buttons | count=13, icon_mode=True | PASS |
| toolbar_no_placeholder_dots | no ellipsis placeholder buttons | 0 | PASS |
| primary_actions_visible | connect/start/stop/export/report visible | True | PASS |
| toolbar_primary_actions_visible | connect/start/stop visible | True | PASS |
| wide_layout_primary_actions_visible | param/help visible when width >= 1366px | width=1280, ok=True | PASS |
| auth_status_not_too_heavy | lightweight auth label, not large chip | label_hint=84x16 | PASS |
| right_status_aligned | auth + window controls on top-right | auth=True, aligned=True | PASS |
| frameless_titlebar_still_active | custom frameless shell | True | PASS |
| top_header_integrated | toolbar embedded in top header | parent=commercialTopHeader | PASS |
| top_header_screenshot_exists | commercial_top_header.png exists | True | PASS |
| top_header_screenshot_exists | commercial_default.png exists | True | PASS |

## Scrollbar / Slider Usability (Default)

**Result: PASS**

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| qss_scrollbar_handle_min_height | >= 24px in QSS | 28px | PASS |
| qss_scrollbar_handle_min_width | >= 24px in QSS | 28px | PASS |
| left_scrollbar_width | >= 12px when visible | 14px | PASS |
| property_scrollbar_width | >= 12px when visible | 14px | PASS |
| log_scrollbar_width | >= 12px when scrollable | 14px | PASS |
| log_area_scrollable | log content scrollable | range=6 | PASS |
| property_area_scrollable | property panel scrollable | range=463 | PASS |
| device_status_scrollable_or_compact | device scroll visible when needed | width=0px | PASS |
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
| custom_title_bar | frameless + title bar visible | custom=True, height=54px | PASS |
| title_bar_height | 48–58 px | 54px | PASS |
| bottom_dock_height | >= 200 px | 200px | PASS |
| log_view_height | >= 100 px | 140px | PASS |
| statistics_panel_height | >= 100 px | 192px | PASS |
| canvas_size | height >= 240px | 616x348px | PASS |
| colorbar_adjacent | gap <= 12 px | 2px | PASS |
| right_panel_width | 340–380 px | 350px | PASS |
| left_panel_width | 220–280 px | 230px | PASS |
| workflow_panel_height | <= 360 px | 257px | PASS |
| device_status_panel_height | expanded content height 120-650 px in left scroll | 624px | PASS |
| left_no_nested_device_scroll | no isolated device-status scroll area | inner_scroll=False | PASS |
| device_status_collapsed_height | collapsed height <= 100 px | 45px | PASS |
| property_tab_bar_fixed | tab bar visible after content scroll | True | PASS |
| numeric_field_line_edit_width | >= 48 px | 52px | PASS |
| numeric_field_total_width | >= 80 px | 80px | PASS |
| scan_action_buttons_layout | start/pause/stop present with no overlap or clipping | count=3, overlap=False, clipped=False | PASS |
| realtime_toolbar_button_text | no "..." labels and width >= 44 px | min_width=52px, ellipsis=False | PASS |
| lut_combo_common_presets | realtime and display LUT combos include Jet/common presets | count=3, include_common=True | PASS |
| center_canvas_priority | canvas >= 1.6x right, >= 2.0x left, area >= 50% | right=1.76x, left=2.68x, area=81% | PASS |
| workspace_wider_than_right_panel | workspace > right panel | 676px > 350px | PASS |
| toolbar_no_overflow | toolbar fits layout | overflow=False | PASS |
| status_bar_visible | status bar visible | True | PASS |
| maximized_window | custom maximized == True | True | PASS |
| target_style_mode | targetStyleMode enabled | true | PASS |
| logo_area_exists | NFS logo block visible | visible=True | PASS |
| top_toolbar_icon_mode | >= 12 toolbar actions | 13 | PASS |
| workflow_timeline_mode | >= 7 timeline steps | 7 | PASS |
| right_compact_grid_form | property tabs + scan region grid/table | tabs=True, rows=1 | PASS |
| bottom_dock_three_panel_mode | tri-panel dock visible | visible=True | PASS |
| spectrum_panel_visible | spectrum panel visible | visible=True | PASS |
| spectrum_yellow_curve_mode | yellow curve spectrum widget | true | PASS |
| scan_stats_panel_visible | scan stats panel visible | visible=True | PASS |
| scan_stats_demo_values | seeded runtime stat values | 2.450 GHz | PASS |
| log_panel_visible | log panel visible with >= 6 lines | lines=13 | PASS |
| log_category_tags | INFO/WARN/ERROR/SCAN/DATA tags | True | PASS |
| pcb_like_mock_board | photo layer mock board loaded | photo_layer_ready | PASS |
| heatmap_smooth_mode | heatmap overlay enabled | 1 | PASS |
| roi_control_points_visible | ROI overlay items present | 9 | PASS |
| right_panel_no_horizontal_clip | property panel fits viewport width | True | PASS |
| scan_progress_bar_visible | runtime progress bar in dock | visible=True | PASS |
| canvas_axis_legend | axis legend visible | visible=True | PASS |
| canvas_cursor_hud | cursor HUD visible | visible=True | PASS |
| minimap_title_visible | MiniMap title "全局视图" | 全局视图 | PASS |
| header_matches_target_mode | targetStyleMode enabled on shell and toolbar | shell=true, toolbar=true | PASS |
| overflow_hidden_at_default_width | overflow hidden when width >= 1500px | width=1280px, overflow=True | PASS |
| toolbar_separator_count_reasonable | strong separators <= 4 | 4 | PASS |
| toolbar_button_width_reasonable | visible buttons width >= 56px | min=60px | PASS |
| toolbar_no_text_touching | adjacent buttons gap >= 4px | count=10, min_gap>=4px | PASS |
| brand_logo_exists | NFS logo square >= 40px | logo=True, size=44x44 | PASS |
| brand_logo_widget_used | NFSLogoWidget or brandLogoWidget property | widget=True, prop=True | PASS |
| brand_logo_not_plain_label | logo is not a plain QLabel text block | plain_label=False | PASS |
| toolbar_custom_icons_used | all toolbar buttons use customToolIcon | custom=13/13 | PASS |
| toolbar_no_qt_default_icon_mode | Qt standard icons not used for toolbar actions | True | PASS |
| auth_status_lightweight | lightweight auth label, not large chip | label_hint=84x16 | PASS |
| brand_logo_blue_enough | brandLogoBlue property on logo tile | brandLogoBlue=True | PASS |
| brand_logo_blue_block | blue brand logo block, not flat black | brandBlueBlock=True | PASS |
| brand_title_hierarchy | CN title + EN subtitle + version badge | title=True, subtitle=True, badge=True, hierarchy=True | PASS |
| brand_not_flat_text | brand is not a single flat text row | flat=False | PASS |
| version_badge_exists | v* version badge visible | v1.0.0 | PASS |
| top_header_height_consistent | 48–58px | 54px | PASS |
| toolbar_button_text_not_overlapping | visible toolbar buttons do not overlap | count=10, min_gap>=2px | PASS |
| toolbar_caption_readable | short readable captions, width >= 56px | count=10, width=60px | PASS |
| toolbar_icon_mode | icon-above-text tool buttons | count=13, icon_mode=True | PASS |
| toolbar_no_placeholder_dots | no ellipsis placeholder buttons | 0 | PASS |
| primary_actions_visible | connect/start/stop/export/report visible | True | PASS |
| toolbar_primary_actions_visible | connect/start/stop visible | True | PASS |
| wide_layout_primary_actions_visible | param/help visible when width >= 1366px | width=1280, ok=True | PASS |
| auth_status_not_too_heavy | lightweight auth label, not large chip | label_hint=84x16 | PASS |
| right_status_aligned | auth + window controls on top-right | auth=True, aligned=True | PASS |
| frameless_titlebar_still_active | custom frameless shell | True | PASS |
| top_header_integrated | toolbar embedded in top header | parent=commercialTopHeader | PASS |
| top_header_screenshot_exists | commercial_maximized.png exists | True | PASS |

## Overall: PASS
