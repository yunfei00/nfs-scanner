# Commercial UI Visual Report

- Generated: 2026-06-26 00:17:33
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
| right_panel_width | 320–460 px | 380px | PASS |
| left_panel_width | 240–330 px | 280px | PASS |
| workspace_wider_than_right_panel | workspace > right panel | 596px > 380px | PASS |
| default_window_within_screen | window <= available screen | 1280x720 <= 1280x720 | PASS |

## Maximized Window

**Result: PASS**

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| custom_title_bar | frameless + title bar visible | custom=True, height=34px | PASS |
| title_bar_height | 28–44 px | 34px | PASS |
| bottom_dock_height | >= 195 px | 195px | PASS |
| log_view_height | >= 100 px | 111px | PASS |
| statistics_panel_height | >= 100 px | 149px | PASS |
| right_panel_width | 320–460 px | 380px | PASS |
| left_panel_width | 240–330 px | 280px | PASS |
| workspace_wider_than_right_panel | workspace > right panel | 596px > 380px | PASS |
| maximized_window | isMaximized() == True | True | PASS |

## Overall: PASS
