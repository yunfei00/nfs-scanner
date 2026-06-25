# Sprint 023–026 — Custom Title Bar & Visual Self-Check

Date: 2026-06-26

## Summary

| Sprint | Result |
|--------|--------|
| 023 Custom Title Bar | Frameless shell + `CommercialTitleBar` (drag, min/max/close) |
| 024 Default Layout Polish | 1600×900 default, 280/380 panels, screen clamp, compact 720p rules |
| 025 Visual Self-Check | `tools/commercial_ui_visual_check.py` + layout metrics |
| 026 Fix Until Pass | Visual check **PASS** (1 round) |

## Visual Check

- Report: `.ai/visual_check/commercial_ui_visual_report.md` — **PASS**
- Screenshots: `.ai/visual_check/commercial_default.png`, `commercial_maximized.png` (gitignored)

## Tests

- 138 unittest OK
- `python tools/commercial_ui_visual_check.py` — exit 0

## Notes

- DWM dark title bar (`window_chrome.py`) retained but commercial UI now uses frameless custom bar.
- Legacy UI unchanged (native title bar).
