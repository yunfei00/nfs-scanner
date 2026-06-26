# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Commercial Header Asset Polish**

顶部品牌 Logo 与工具栏图标资产收敛：自绘 `NFSLogoWidget` + 内部 `ToolIconFactory`；QA 增加 logo/icon 检查；主体区域未改。

## Recent (2026-06-26)

- `NFSLogoWidget`：44×44 QPainter 蓝色渐变 + 六边形 + NFS 字样
- `ToolIconFactory`：13 种工具栏线性图标，替换 Qt 标准图标
- QA 修正 logo 检测类型（QWidget 非 QFrame）
- 148 tests + visual + QA PASS

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
| Commercial Header Asset Polish | **done** |
| Real Motion Control | **blocked** |

## Constraints (unchanged)

- No motion commands; no real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
