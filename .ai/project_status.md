# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Header Readability Fix**

商业 UI 顶部可读性修复：工具栏短标签+宽按钮、蓝色 NFS logo、轻量授权状态；QA PASS。

## Recent (2026-06-26)

- 工具栏：62×48 按钮、5px 间距、短标签（新建/连接/开始…）+ 完整 tooltip
- Logo：亮蓝渐变 + WA_StyledBackground，42×42 品牌块
- 右上：绿点 +「授权状态：正常」轻量文本（DRY RUN 在 tooltip）
- QA：toolbar 重叠/可读性、brand_logo_blue_block、auth_status_not_too_heavy

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
| Top Header Final Polish | **done** |
| Real Motion Control | **blocked** |

## Constraints (unchanged)

- No motion commands; no real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
