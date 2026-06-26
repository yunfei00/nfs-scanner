# Final Delta Polish — Target Screenshot Alignment

Date: 2026-06-26

## Summary

针对当前 commercial UI 与目标截图的 8 类差异做最后一轮高保真对齐，不接真实设备。

## Changes

| Diff | Area | Highlights |
|------|------|------------|
| 01 | Title + Toolbar | 32px 紧凑标题栏、克制 Demo 条、50×34 工具按钮、绿/红扫描强调 |
| 02 | Central Canvas | 照片感 PCB mock、Turbo 热图、ROI/路径对比度、MiniMap 缩略板卡 |
| 03 | Left Workflow | 230px 左栏、紧凑 timeline、设备地址行 |
| 04 | Right Panel | 56px 紧凑输入、2×2 统计卡、demo 数值锁定 |
| 05 | Bottom Dock | 三栏比例、日志最小高度、频谱 M1 |
| 06 | Canvas Toolbar | 选择/平移/缩放等 10 项小按钮 + 透明度/LUT |
| 07 | Status Bar | 绿点系统态、日期时间、Mock/授权/模式 chip |
| 08 | Scroll/Slider | handle min 28px 可拖动、tracking、QA smoke |

## Verification

- `python -m compileall nfs_scanner` — OK
- `python -m unittest discover -s tests` — 145 PASS
- `tools/commercial_ui_visual_check.py` — PASS
- `tools/qa_run_commercial_demo.py` — PASS

## Screenshots

- Default: `.ai/qa/latest/screenshots/commercial_default.png`
- Maximized: `.ai/qa/latest/screenshots/commercial_maximized.png`
