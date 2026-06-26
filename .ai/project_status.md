# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Top Header Target Alignment**

商业 UI 顶部已对齐目标图：42×42 NFS logo 品牌块 + 52px 一体化 header + 图标工具栏 + 右上授权/窗口控制；visual/QA 自检 PASS。

## Recent (2026-06-26)

- `CommercialBrandArea`：蓝色 NFS logo 方块 + 中文主标题 + 英文副标题 + v1.0.0 badge（层级清晰）
- `CommercialTopHeader` 52px：品牌区 / 工具栏 / 授权-Admin-窗口控制 同一顶栏
- 工具栏 13 项：52×48 图标在上文字在下，分组分隔，绿/红/蓝主操作强调
- 顶部 QA 10 项检查 + `top_header.png` 特写截图

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
| Top Header Target Alignment | **done** |
| Real Motion Control | **blocked** |

## Constraints (unchanged)

- No motion commands; no real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
