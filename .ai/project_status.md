# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Final Delta Polish (Target Screenshot Alignment)**

商业 UI 已完成最后一轮 8 类差异高保真对齐；默认/最大化截图 + QA 自检 PASS。

## Recent (2026-06-26)

- Final Delta Polish：紧凑 title/toolbar、照片感 PCB+Turbo 热图、230px workflow、仪器参数区、三栏 dock、可拖动滚动条
- 145 tests + visual check + QA pipeline **PASS**

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
| Real Motion Control | **blocked** |

## Constraints (unchanged)

- No motion commands; no real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
