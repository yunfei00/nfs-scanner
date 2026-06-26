# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Commercial Demo v0.2 Functional Completion**

商业 UI Mock Demo 功能闭环已完成：项目会话、设备中心、扫描参数、Mock 运行时、实时视图、Data View、Report Center、Reset Demo、QA 全流程验证。顶部 Header 已冻结。

## Recent (2026-06-26)

- Mock 项目 JSON 保存（含 scan_config / device_summary）
- 设备中心 + 扫描运行时 + Data/Report 导出闭环
- QA pipeline 覆盖 start/pause/resume/complete/export/reset
- 149 tests + visual + QA PASS

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
| Commercial Header Asset Polish | **done** |
| **Commercial Demo v0.2** | **done** |
| Real Motion Control | **blocked** |

## Manual Acceptance

见 `.ai/daily/2026-06-26-commercial-demo-v0.2-functional-completion.md`

## Constraints (unchanged)

- No motion commands; no real spectrum/camera/scan/CSV changes.
- `REAL_DEVICE_ENABLED=false` by default.
