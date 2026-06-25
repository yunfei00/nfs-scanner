# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Demo v0.1 + Custom Title Bar + Visual Self-Check (Sprint 023–026)**

商业版使用自定义深色 frameless 标题栏；布局自检工具可自动截图并 PASS/FAIL 报告。

## Recent (2026-06-26)

- `CommercialTitleBar` — 拖动、最小化、最大化/还原、关闭
- Frameless `CommercialMainShell`（仅商业 UI）
- 默认窗口 1600×900（小屏适配 + 屏幕边界 clamp）
- `tools/commercial_ui_visual_check.py` — 自动截图 + 布局指标断言

## Application Entry Points

- Legacy UI (default): `python -m nfs_scanner.main`
- Commercial Demo UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`
- Visual self-check: `python tools/commercial_ui_visual_check.py`

## Sprint Progress

| Sprint | Status |
|--------|--------|
| 001–022 | done — Demo 闭环 v0.1 |
| 023 | done — Custom title bar |
| 024 | done — Default layout polish |
| 025 | done — Visual self-check tool |
| 026 | done — Visual check PASS |
| Real Motion Control | **blocked** |

## Constraints (unchanged)

- No motion commands; no real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
