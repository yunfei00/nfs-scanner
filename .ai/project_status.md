# Project Status

Last updated: 2026-06-25

## Current Mode

**COMPLETE — Demo 闭环 v0.1 + UI Polish (bottom dock / title bar)**

商业版 Mock Demo 可演示；2026-06-25 修复底部 dock 高度、日志/统计可读性、Windows 深色标题栏。

## Recent UI Polish (2026-06-25)

- Windows DWM dark title bar (`window_chrome.py`)
- Bottom dock 默认 ~30% 高度（min 200px），stretch 7:3
- 日志 Tab 默认打开、8 行种子、自动滚动
- 统计 Tab 双列卡片：预览 + 运行时（含进度%）
- 工具栏压缩、mini-map 边框弱化

## Sprint Progress

| Sprint | Status | Notes |
|--------|--------|-------|
| Sprint 001–015 | done | Shell, mock scan, device center, dry-run, motion connection test |
| Sprint 016 | done | Commercial UI visual polish |
| Sprint 017 | done | Mock project workflow |
| Sprint 018 | done | Full mock scan demo loop |
| Sprint 019 | done | Data view with mock charts |
| Sprint 020 | done | Report center Markdown export |
| Sprint 021 | done | Demo banner + reset |
| Sprint 022 | done | Final overnight review |
| Real Motion Control | **blocked** | Major Review required |

## Application Entry Points

- Legacy UI (default): `python -m nfs_scanner.main`
- Commercial Demo UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`
- Autoclose (CI/smoke): `NFS_SCANNER_AUTOCLOSE_MS=1500 python -m nfs_scanner.main`

## Demo Capabilities

- MockProjectService: new / open / save metadata JSON
- MockScanController: start / pause / resume / stop
- MockAnalysisService: task registry + summaries
- MockReportService: preview + Markdown export to `~/.nfs_scanner/reports/`
- DemoSessionController: one-click reset

## Constraints (unchanged)

- No motion commands (home/jog/move/G-code).
- No real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.

## Next Actions (Human)

1. Manual demo walkthrough (see `.ai/daily/overnight-final-review.md`)
2. Approve or defer real motion control Sprint
