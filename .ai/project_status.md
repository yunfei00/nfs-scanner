# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Top Header Target Match Final**

商业 UI 顶部最终收敛：宽屏无 overflow、弱分隔线、自绘 NFS logo、稳定工具栏；QA 加强 overflow/separator 检查。

## Recent (2026-06-26)

- >=1500px 隐藏 overflow；仅次要 mock 项可收纳
- 工具栏 2 条内部分隔 + 透明背景；按钮 60×50
- NFSBrandLogoFrame 蓝色渐变自绘 logo
- QA：overflow_hidden_at_default_width、separator<=4、gap>=4

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
| Header Readability Fix | **done** |
| Top Header Target Match Final | **done** |
| Real Motion Control | **blocked** |

## Constraints (unchanged)

- No motion commands; no real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
