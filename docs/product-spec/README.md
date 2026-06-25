# Near Field Scanner Product Specification

本目录是 NFS Scanner 商业版界面与功能实现的单一事实来源（Single Source of Truth）。

目标是让 Codex / Cursor / Claude Code / ChatGPT 在同一套规范下持续开发，避免每次对话重新解释需求。

## 文档结构

- `00_product_vision.md`：产品定位、用户、边界、成功标准。
- `01_design_system.md`：主题、颜色、字号、间距、组件规范。
- `02_main_window_layout.md`：主窗口布局、响应式规则、Dock/Panel 策略。
- `03_work_modes.md`：实时视图、数据视图、3D 视图、数据表格、报告中心、设备中心。
- `04_feature_specs.md`：核心功能规格：扫描、相机对齐、热力图、Marker、仪表、数据存储。
- `05_implementation_roadmap.md`：分阶段实现路线。
- `06_codex_tasks.md`：可直接交给 Codex 连续执行的任务清单。
- `../../.ai/codex.md`：AI 开发规则与执行方式。

## 总体原则

1. 软件不是简单上位机，而是企业级近场扫描平台。
2. 中央画布永远是视觉核心，参数和日志不能抢占画布。
3. 每个工作模式只解决一类任务：实时扫描、离线分析、三维展示、数据表格、报告生成、设备管理。
4. UI 必须同时适配笔记本和台式机：1366×768 可用，1920×1080 舒服，2K/4K 更佳。
5. 所有新功能必须有验收标准，不允许只实现“看起来像”。
