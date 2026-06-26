# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Commercial Demo v0.3 Functional Hardening**

Mock Demo 功能稳定化：状态一致性同步、日志节流、Data/Report 验收深化、QA 全流程增强。Header 冻结。

## Recent (2026-06-26)

- `demo_state_sync.py` workflow/status bar 统一
- 去除启动伪造 65% 扫描进度
- QA 新增 progress>5%、stop、reset_demo 截图
- manual acceptance + state audit 文档

## Application Entry Points

- Legacy UI (default): `python -m nfs_scanner.main`
- Commercial Demo UI: `NFS_SCANNER_UI=commercial python -m nfs_scanner.main`
- Visual self-check: `python tools/commercial_ui_visual_check.py`
- **QA Pipeline**: `python tools/qa_run_commercial_demo.py`

## Manual Acceptance

`.ai/reviews/commercial_demo_v0_3_manual_acceptance.md`

## Sprint Progress

| Sprint | Status |
|--------|--------|
| Commercial Demo v0.2 | **done** |
| **Commercial Demo v0.3** | **done** |
| Real Motion Control | **blocked** |

## Constraints (unchanged)

- No real hardware; `REAL_DEVICE_ENABLED=false`
