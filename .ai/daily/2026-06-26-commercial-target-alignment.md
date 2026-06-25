# 商业目标页面对齐 — Commercial Target Alignment

Date: 2026-06-26

## Summary

按 10 项 UI 验收标准完成商业版界面对齐，使用户可直接做功能验收，无需逐项检查 UI 小问题。

## Changes

| Area | Change |
|------|--------|
| Toolbar | 主/次按钮分组；≤1366px 文件操作 overflow 菜单；初始 disable 暂停/停止/导出 |
| Status Bar | 紧凑 chip：System Ready / Mock Runtime / 项目 / 任务 / 进度 / Real Device / Trial / 时间 |
| Left Panel | Workflow 固定 + 设备状态独立 QScrollArea（max 240px） |
| Realtime View | ColorBar 间距 2px；canvas min height 260px |
| Layout Metrics | canvas/colorbar/toolbar overflow/status bar 检查 |
| QSS | toolbar 分组、status chip、workflow pending 态、device scroll |

## Visual Check

- Report: `.ai/visual_check/commercial_ui_visual_report.md` — **PASS**
- Default + maximized screenshots generated (PNG gitignored)

## Tests

- 138 unittest OK
- `python tools/commercial_ui_visual_check.py` — exit 0

## Constraints (unchanged)

- No real devices, motion, spectrum, camera, ScanManager, CSV changes
- Legacy UI unchanged
