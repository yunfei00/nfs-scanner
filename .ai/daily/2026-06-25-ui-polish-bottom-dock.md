# UI Polish — Bottom Dock & Title Bar

Date: 2026-06-25

## Tasks

| Task | Summary |
|------|---------|
| 01 | Windows DWM dark title bar via `window_chrome.apply_dark_title_bar` |
| 02 | Bottom dock ~30% height, min 200px, stretch 7:3, removed 240px cap |
| 03 | Log tab compact layout, 8 seed lines, auto-scroll, default tab |
| 04 | Statistics two-column panels with preview + runtime metrics |
| 05 | Toolbar 52px, softer mini-map, dock QSS |

## Tests

- compileall OK
- 136 unittest OK
- legacy + commercial GUI autoclose OK
