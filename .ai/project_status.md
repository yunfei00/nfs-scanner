# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Target Screenshot Layout Replication**

商业 UI 已按目标图结构重构：顶部工具栏、左侧 timeline、中央 PCB+heatmap、右侧紧凑参数 Tab、底部三栏 dock。

## Recent (2026-06-26)

- 目标图对齐：title bar + 13 项工具栏 + 授权区
- 画布：PCB mock 满幅、白路径、ROI、MiniMap 绿框
- 参数面板 350px 三 Tab + XYZ 网格
- 底部频谱/统计/日志三栏 + QA 15+ 检查项
- visual check + QA pipeline **PASS**

## Application Entry Points

- Legacy UI (default): `python -m nfs_scanner.main`
- Commercial Demo UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`
- Visual self-check: `python tools/commercial_ui_visual_check.py`
- **QA Pipeline**: `python tools/qa_run_commercial_demo.py`

## Sprint Progress

| Sprint | Status |
|--------|--------|
| 001–022 | done — Demo 闭环 v0.1 |
| Commercial Target Alignment | **done** |
| Target Screenshot Replication | **done** |
| Real Motion Control | **blocked** |

## Constraints (unchanged)

- No motion commands; no real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
