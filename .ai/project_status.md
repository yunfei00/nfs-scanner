# Project Status

Last updated: 2026-06-26

## Current Mode

**COMPLETE — Top Header Final Polish**

商业 UI 顶部最后一轮 polish：品牌区/logo/工具栏/右上状态精修；QA title_bar_height 期望修正为 48–58px；visual/QA PASS。

## Recent (2026-06-26)

- 品牌区：42×42 渐变 NFS logo + 中文标题 + v badge + 英文副标题（232px）
- 工具栏：54×48 六组仪器风格按钮，mock 项弱化样式
- 右上：`授权状态：正常` + Admin + 窗口控制（DRY RUN 在 tooltip）
- QA：`title_bar_height` 期望 48–58px 与判定一致；新增 version_badge / screenshot 检查

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
