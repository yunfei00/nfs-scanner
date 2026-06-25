# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Commercial Target Page Alignment (Canvas Priority)**

中央实时画布成为视觉中心；左右侧栏压缩，bottom dock 平衡；visual check + QA pipeline 含 `center_canvas_priority` 断言。

## Recent (2026-06-26)

- 左栏 240px / 右栏 320px（原 280/380）
- Bottom dock ratio 24%/20%（原 28%/22%），center splitter 8:2
- `center_canvas_priority`：canvas >= 1.6x 右栏、>= 2.0x 左栏、面积 >= 50%
- 720p 下 canvas 636×307，area ratio 81%

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
