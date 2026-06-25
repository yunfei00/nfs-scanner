# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — 商业目标页面对齐 (Commercial Target Alignment)**

商业版 UI 已对齐用户确认的商业版目标图验收标准：自定义深色标题栏、主次工具栏、三态 workflow、中央实时视图、底部 Dock、状态栏 chip、visual self-check PASS。

## Recent (2026-06-26)

- Toolbar 主/次分组 + 1366px overflow
- Status bar 紧凑 chip 布局
- 左侧 workflow + 可滚动设备状态
- Layout metrics 扩展（canvas / colorbar / toolbar / status bar）
- Visual check **PASS**（default + maximized）

## Application Entry Points

- Legacy UI (default): `python -m nfs_scanner.main`
- Commercial Demo UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`
- Visual self-check: `python tools/commercial_ui_visual_check.py`

## Sprint Progress

| Sprint | Status |
|--------|--------|
| 001–022 | done — Demo 闭环 v0.1 |
| 023–026 | done — Custom title bar + visual self-check |
| Commercial Target Alignment | **done** |
| Real Motion Control | **blocked** |

## Constraints (unchanged)

- No motion commands; no real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
