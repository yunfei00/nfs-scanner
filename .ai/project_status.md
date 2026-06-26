# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Unified Top Header Polish**

商业 UI 顶部已合并为单行一体化 header（品牌 + 工具栏 + 授权/窗口控制），visual/QA 自检 PASS。

## Recent (2026-06-26)

- Unified `CommercialTopHeader`：单行品牌（NFS + 中文 + 英文 + v1.0.0）+ 嵌入工具栏 + 授权/Admin/窗口按钮
- 顶部总高度 36px；工具按钮 46×32
- 顶部特写截图 QA：`commercial_top_header.png`

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
| Final Delta Polish | **done** |
| Unified Top Header | **done** |
| Real Motion Control | **blocked** |

## Constraints (unchanged)

- No motion commands; no real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
