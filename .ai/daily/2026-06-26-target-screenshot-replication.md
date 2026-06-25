# 2026-06-26 — Target Screenshot Layout Replication

## 目标

按用户目标图重构商业 UI 五区布局（顶/左/中/右/底），不接真实设备。

## 完成项

- Task 01: 标题栏（品牌+授权+用户）+ 13 项 Qt 图标工具栏
- Task 02: PCB mock 满幅、白蛇形路径、ROI、MiniMap 缩略图+绿框、扫描信息 HUD
- Task 03: Timeline 勾号/进行中进度、目标 demo 状态 65.2%
- Task 04: 三 Tab 参数面板、XYZ 紧凑网格、2×2 统计卡
- Task 05: 黄色频谱曲线+M1、扫描统计 seed、日志分类标签
- Task 06: 350px 右栏、240px 底 dock、全局 QSS 密度
- Task 07: target_alignment_metrics 扩展 + visual/QA PASS

## 验证

- unittest 145 PASS
- commercial_ui_visual_check PASS
- qa_run_commercial_demo PASS
