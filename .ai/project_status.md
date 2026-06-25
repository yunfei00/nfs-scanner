# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Commercial Scrollbar / Slider UX Alignment**

商业 UI 滚动条/滑块统一加粗（14px）、handle 最小 48px、hover/pressed 清晰；QA 含 scrollbar 可用性检查。

## Recent (2026-06-26)

- 全局 QScrollBar/QSlider/QProgressBar QSS 重写
- `scroll_helpers.py` + 各区域 scroll 配置
- `scroll_metrics.py` + QA interaction 检查
- 720p visual + QA **PASS**

## Application Entry Points

- Legacy UI (default): `python -m nfs_scanner.main`
- Commercial Demo UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`
- Visual self-check: `python tools/commercial_ui_visual_check.py`
- **QA Pipeline**: `python tools/qa_run_commercial_demo.py`

## Sprint Progress

| Sprint | Status |
|--------|--------|
| 001–022 | done — Demo 闭环 v0.1 |
| 023–026 | done — Custom title bar + visual self-check |
| Commercial Target Alignment | **done** |
| Commercial Demo QA Pipeline | **done** |
| Real Motion Control | **blocked** |

## Constraints (unchanged)

- No motion commands; no real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
