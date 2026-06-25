# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Commercial Demo QA Pipeline**

商业版 UI 已对齐目标图验收标准；新增 `tools/qa_run_commercial_demo.py` 自动完成启动检查、mock 流程、截图、布局断言与安全检查。

## Recent (2026-06-26)

- Commercial Demo QA Pipeline (`tools/qa_run_commercial_demo.py`)
- 输出 `.ai/qa/latest/qa_report.md` + `qa_result.json` + 截图
- 自动修复循环（最多 3 轮，blocked 项立即停止）
- Toolbar 主/次分组 + 1366px overflow（商业目标对齐）

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
